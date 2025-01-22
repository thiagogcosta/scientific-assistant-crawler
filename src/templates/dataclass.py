from pydantic import BaseModel


class ArticleInfo(BaseModel):
    name: str
    page_link: str
    pdf_download_link: str
    author_keywords: str
    publication_date: str
    doi: str
    filename: str
