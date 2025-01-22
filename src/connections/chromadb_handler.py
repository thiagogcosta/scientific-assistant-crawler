import chromadb
import logfire
from chromadb.config import Settings

from src.connections.config import Config
from src.connections.utils import (
    get_document_list,
    get_embedding_function,
    get_id_list,
    get_metadata_list,
    get_text_list,
)
from src.logger import Logger
from src.templates.chromadb_base import ChromaDBBase

# --------------------------
# -----DESC: Logger-----
logger = Logger().get_logger()
# --------------------------


# ChromaDB
class ChromaDBHandler(ChromaDBBase):
    def connect(self, *, config: Config) -> chromadb.HttpClient:
        host = f'http://{config.chroma_host}:{config.chroma_port}'

        client = chromadb.HttpClient(
            host=host,
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False,
                chroma_client_auth_provider=config.chroma_client_auth_provider,
                chroma_client_auth_credentials=config.chroma_client_auth_credentials,
                chroma_auth_token_transport_header=config.chroma_auth_token_transport_header,
            ),
        )

        return client

    def insert(
        self,
        *,
        config: Config,
        client: chromadb.HttpClient,
        document_chunks,
        embedding_model_name: str,
    ):
        document_collection = client.get_or_create_collection(
            name=config.chroma_collection,
            embedding_function=get_embedding_function(
                embedding_model_name=embedding_model_name
            ),
        )

        # DESC: get the document list
        document_list = get_document_list(document_chunks=document_chunks)

        # DESC: get the document ids
        document_ids = get_id_list(document_list=document_list)

        # DESC: get the text of the documents
        document_texts = get_text_list(document_list=document_list)

        # DESC: get the metadatas of the documents
        document_metadatas = get_metadata_list(document_list=document_list)

        # DESC: Add the documents inside the ChromaDB
        # throught the configured collection
        try:
            for i in range(len(document_ids)):
                metadata = {
                    'doi': document_list[i].metadata.get('doi', ''),
                    'publication_date': document_list[i].metadata.get(
                        'publication_date', ''
                    ),
                    'page': document_list[i].metadata.get('page', ''),
                    'start_index': document_list[i].metadata.get('start_index', ''),
                }

                # FIXME: Acho interessante verificarmos se os
                # documentos existem no ChromaDB em Batch...

                # DESC: Filtro para verificar se já existe um documento
                # com este ID inserido no ChromaDB
                document = document_collection.get(
                    ids=[document_ids[i]],
                    include=['metadatas', 'documents', 'embeddings'],
                )

                # FIXME: Acho interessante inserirmos os dados
                # no ChromaDB em Batch...

                # DESC: caso não tenha sido encontrado ids
                # para o document recuperado
                if not document.get('ids', None):
                    document_collection.add(
                        ids=document_ids[i],
                        documents=document_texts[i],
                        metadatas=document_metadatas[i],
                    )

                    logger.info('-' * 10)
                    logger.info(
                        f'SUCCESS - Document inserted with success: ID={document_ids[i]}, metadata={metadata}'
                    )
                    logger.info('-' * 10)
                    logfire.info(
                        f'SUCCESS - Document inserted with success: ID={document_ids[i]}, metadata={metadata}',
                        doi=metadata['doi'],
                        publication_date=metadata['publication_date'],
                    )

                else:
                    logger.info('-' * 10)
                    logger.info(
                        f'ERROR - Document already exists: ID={document_ids[i]}, metadata={metadata}'
                    )
                    logger.info('-' * 10)
                    logfire.exception(
                        f'ERROR - Document already exists: ID={document_ids[i]}, metadata={metadata}',
                        doi=metadata['doi'],
                        publication_date=metadata['publication_date'],
                    )

        except chromadb.errors.DuplicateIDError as e:
            logger.info('-' * 10)
            logger.info(f'ERROR - DuplicateIDError occurred: {e}')
            logger.info('-' * 10)
            logfire.exception(f'ERROR - DuplicateIDError occurred: {e}')

            pass
