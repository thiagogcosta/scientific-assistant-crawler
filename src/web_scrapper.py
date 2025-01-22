import os
from typing import List

import logfire
import wget
from langchain.schema import Document
from selenium.common.exceptions import (
    WebDriverException,
)
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.connections.chromadb_handler import ChromaDBHandler
from src.connections.config import Config
from src.templates.dataclass import ArticleInfo
from src.templates.web_scrapper_base import WebScrapperBase
from src.utils import (
    get_article_document,
    get_article_name,
    get_article_number,
    get_donwload_link,
    get_infos,
    get_page_link,
    journal_issue_verify,
)

# -----DESC: Logfire Config-----
logfire.configure(
    token=os.environ.get('LOGFIRE_PROJECT_TOKEN', ''),
    pydantic_plugin=logfire.PydanticPlugin(record='all'),
)
# ------------------------------


# WebScrapper
class WebScrapper(WebScrapperBase):
    def config(self, number: int = 3, year: int = 2024):
        self.config = Config()
        self.number = number
        self.year = year

        # --------------------
        # Journal:
        # - name: Advances in Electrical and Computer Engineering
        # - link: https://aece.ro/index.php
        # --------------------

        # ---------------Chrome Config---------------
        self.chrome_options = Options()

        # Dont Open Screen
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--no-sandbox')
        # -------------------------------------------

        return {
            'driver': Chrome(options=self.chrome_options),
            'url': f'https://aece.ro/displayissue.php?year={self.year}&number={self.number}',
        }

    def conectar(self, url: str, driver: Chrome):
        # ---------------Chrome Access---------------
        driver.get(url)

        return driver

    def captar(self, driver: Chrome) -> List[Document]:
        # DESC: Verificação se a issue do journal é válida
        journal_issue_verify(
            number=self.number,
            year=self.year,
            driver=driver,
        )

        elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'papertitle1'))
        )

        documents_list = []

        for i in range(len(elements)):
            # -------------------------
            # DESC: Obtenção do nome do artigo
            article_name = get_article_name(element=elements[i])
            # -------------------------

            # -------------------------
            # DESC: Obtenção do link da página do artigo
            article_page_refence = f'https://aece.ro/abstractplus.php?year={self.year}&number={self.number}'
            page_link = get_page_link(
                element=elements[i], reference=article_page_refence
            )
            # -------------------------

            # -------------------------
            # DESC: Criar um novo driver
            new_driver = Chrome(options=self.chrome_options)
            # -------------------------

            # -------------------------
            # DESC: acessar a página do artigo científico
            new_driver = self.conectar(url=page_link, driver=new_driver)
            # -------------------------

            # -------------------------
            # DESC: Obtenção de author keywords
            author_keywords = get_infos(driver=new_driver, topic='Author keywords')
            # -------------------------

            # -------------------------
            # DESC: Obtenção da data de publicação
            date_of_publication = get_infos(
                driver=new_driver, topic='Date of Publication'
            )
            # -------------------------

            # -------------------------
            # DESC: Obtenção da data de publicação
            doi = get_infos(driver=new_driver, topic='Digital Object Identifier')
            # -------------------------

            # -------------------------
            # DESC: Obtenção dos links dos PDF's dos artigos científcos
            article_link_refence = (
                f'https://aece.ro/displaypdf.php?year={self.year}&number={self.number}'
            )
            article_links = get_donwload_link(
                driver=new_driver, reference=article_link_refence
            )
            # -------------------------

            # -------------------------
            # DESC: Download dos artigos científcos
            try:
                article_download_link = article_links[0]
                article_number = get_article_number(link=article_download_link)

                file_path = f'/tmp/year_{self.year}_number_{self.number}_article_{article_number}.pdf'

                filename = wget.download(article_download_link, file_path)

            except IndexError:
                # DESC: Close connection if article does not have a download link
                new_driver.close()
                break
            # -------------------------

            # -------------------------
            # DESC: Create ArticleInfo object
            article_info = ArticleInfo(
                name=article_name,
                page_link=page_link,
                pdf_download_link=article_download_link,
                author_keywords=author_keywords,
                publication_date=date_of_publication,
                doi=doi,
                filename=filename,
            )
            # -------------------------

            # -------------------------
            # DESC: Langchain Document a partir dos dados crawleados
            article_document = get_article_document(article_info=article_info)

            # -------------------------

            documents_list.append(article_document)

            # -------------------------
            # DESC: Fechar driver
            new_driver.close()
            # -------------------------

        return documents_list

    def persistir(self, *, document_chunks, embedding_model_name: str):
        chroma_db_handler = ChromaDBHandler()

        client = chroma_db_handler.connect(config=self.config)

        chroma_db_handler.insert(
            config=self.config,
            client=client,
            document_chunks=document_chunks,
            embedding_model_name=embedding_model_name,
        )

    def execute(self, *, number: int, year: int):
        config_dict = self.config(number=number, year=year)

        driver = self.conectar(url=config_dict['url'], driver=config_dict['driver'])

        document_chunks = self.captar(driver=driver)

        # DESC: Raise an exception if scientific journal
        # does not have a download link
        if not document_chunks:
            logfire.exception(
                'Journal without a pdf download link, please, inform an issue and year that has pdf download link!'
            )
            raise WebDriverException(
                'Journal without a pdf download link, please, inform an issue and year that has pdf download link!'
            )

        self.persistir(
            document_chunks=document_chunks,
            embedding_model_name=self.config.embedding_model_name,
        )

        driver.close()
