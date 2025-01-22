import re
from typing import List

from chromadb.utils import embedding_functions
from chromadbx import DocumentSHA256Generator
from langchain.docstore.document import Document


# DESC: Transform documents matrix into documents list
def get_document_list(*, document_chunks):
    return [docs for docs_list in document_chunks for docs in docs_list]


# DESC: Geração do document_id, inclusive vários
# documentos vão ter o mesmo DOI, pois estamos armazenando chunks,
# logo é mais interessanter colocar informações
# complementares aos chunks: doi, source, page...
def _get_document_id(*, document_chunk: Document):
    doi = document_chunk.metadata.get('doi', '')
    publication_date = document_chunk.metadata.get('publication_date', '')
    page = document_chunk.metadata.get('page', '')
    start_index = document_chunk.metadata.get('start_index', '')

    document_name = '_'.join(
        str(item) for item in [doi, publication_date, page, start_index]
    )

    return DocumentSHA256Generator(documents=[document_name])[0]


# DEF: Get the document ids
def get_id_list(*, document_list: List[Document]):
    return [
        _get_document_id(document_chunk=document_chunk)
        for document_chunk in document_list
    ]


# DEF: Preprocess the text
def _get_preprocessed_text(*, text):
    new_text = text.replace('\n', '')

    return re.sub('[^a-zA-Z0-9áéíóúÁÉÍÓÚâêîôÂÊÎÔãõÃÕçÇ: ]', '', new_text)


# DEF: Get the text list
def get_text_list(*, document_list: List[Document]):
    return [
        _get_preprocessed_text(text=document_chunk.page_content)
        for document_chunk in document_list
    ]


# DEF: Get the metadata list
def get_metadata_list(*, document_list: List[Document]):
    return [document_chunk.metadata for document_chunk in document_list]


# DEF: Get the embedding function
def get_embedding_function(*, embedding_model_name: str):
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=embedding_model_name
    )
