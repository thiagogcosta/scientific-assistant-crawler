import logfire
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from selenium.common.exceptions import (
    InvalidSelectorException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.logger import Logger

# --------------------------
# -----DESC: Logger-----
logger = Logger().get_logger()
# --------------------------


def journal_issue_verify(*, number: int, year: int, driver: Chrome):
    page_source = driver.page_source
    issue_text = f'Issue: <b>{number}</b>'
    year_text = f'Year: <b>{year}</b>'

    logger.info('-' * 10)
    logger.info(f'{issue_text}')
    logger.info(f'{year_text}')
    logger.info('-' * 10)

    logfire.info(f'issue: {issue_text}')
    logfire.info(f'year: {year_text}')

    if issue_text not in page_source or year_text not in page_source:
        if 'Current Issue' in page_source:
            logger.info('-' * 10)
            logger.info('Invalid issue, please inform a valid issue of the journal!')
            logger.info('-' * 10)
            logfire.exception(
                'Invalid issue, please inform a valid issue of the journal!'
            )
            raise WebDriverException


def get_article_name(*, element):
    return element.text.strip()


def get_page_link(*, element, reference: str):
    page_link = None

    try:
        a_tag = element.find_element(By.TAG_NAME, 'a')
        href = a_tag.get_attribute('href')

        if reference in href:
            page_link = href

            return page_link

    except Exception as e:
        logger.info(f'Error extracting href: {e}')
        logfire.exception(f'Error extracting href: {e}')
        pass

    return page_link


def get_donwload_link(*, driver: Chrome, reference: str, timeout: int = 10):
    links = []
    try:
        elements = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.XPATH, '//a[@href]'))
        )

        for element in elements:
            if reference in element.get_attribute('href'):
                links.append(element.get_attribute('href'))

        links = list(set(links))

    except InvalidSelectorException as e:
        logger.info(f'Erro: Invalid selector: {e}')
        logfire.exception(f'Erro: Invalid selector: {e}')

    except TimeoutException:
        logger.info('Erro: Timed out waiting for elements to be present.')
        logfire.exception('Erro: Timed out waiting for elements to be present.')

    return links


def _get_author_keywords(tags):
    # DESC: As palavras-chave dos autores sempre estarão contidos
    # dentro do 'font' que contém a frase: 'Author Keywords'
    return tags[1].text.strip()


def _get_date_of_publication(tags):
    # DESC: A data da publicação sempre estará contida
    # dentro do 'font' que contém a frase: 'About this article'
    preprocess_publication_date = tags[1].get_attribute('outerHTML').split('<br>')[1]
    return preprocess_publication_date.split(':')[-1].replace(' ', '')


def _get_doi(tags):
    # DESC: O DOI sempre estará contido dentro do 'font'
    # que contém a frase: 'About this article'
    preprocess_doi = tags[1].get_attribute('outerHTML').split('<br>')[4]
    return preprocess_doi.split(':')[-1].replace(' ', '').replace('\n', '')


def get_infos(*, driver: Chrome, topic: str = 'Author keywords', timeout: int = 10):
    valid_topics = [
        'Author keywords',
        'Date of Publication',
        'Digital Object Identifier',
    ]

    if topic not in valid_topics:
        logger.info('-' * 10)
        logger.info(
            f'Invalid reference, please, inform a valid reference (such, as {valid_topics})'
        )
        logger.info('-' * 10)
        logfire.exception(
            f'Invalid reference, please, inform a valid reference (such, as {valid_topics})'
        )
        raise WebDriverException

    reference = (
        'About this article' if topic != 'Author keywords' else 'Author keywords'
    )

    try:
        elements = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, 'font'))
        )

        for element in elements:
            outer_html = element.get_attribute('outerHTML')

            if reference in outer_html:
                tags = element.find_elements(By.TAG_NAME, 'font')

                if topic == 'Author keywords':
                    return _get_author_keywords(tags)
                elif topic == 'Date of Publication':
                    return _get_date_of_publication(tags)
                else:
                    return _get_doi(tags)

    except InvalidSelectorException as e:
        logger.info(f'Erro: Invalid selector: {e}')
        logfire.exception(f'Erro: Invalid selector: {e}')

    except TimeoutException:
        logger.info('Erro: Timed out waiting for elements to be present.')
        logfire.exception('Erro: Timed out waiting for elements to be present.')

    return None


def get_article_number(*, link: str):
    return link.split('&')[-1].split('=')[-1]


def _split_text(*, documents: list[Document]):
    # Initialize text splitter with specified parameters
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,  # Size of each chunk in characters
        chunk_overlap=100,  # Overlap between consecutive chunks
        length_function=len,  # Function to compute the length of the text
        add_start_index=True,  # Flag to add start index to each chunk
    )

    # Split documents into smaller chunks using text splitter
    return text_splitter.split_documents(documents)


def get_article_document(*, article_info: Document):
    document_list = [
        Document(
            page_content=document.page_content,
            metadata={
                'doi': str(article_info.doi),
                'name': str(article_info.name),
                'publication_date': str(article_info.publication_date),
                'keywords': str(article_info.author_keywords),
                'source': str(document.metadata['source']),
                'page': str(document.metadata['page']),
            },
        )
        for document in PyPDFLoader(article_info.pdf_download_link).load()
    ]

    return _split_text(documents=document_list)
