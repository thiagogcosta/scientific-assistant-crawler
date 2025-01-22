import os

import chromadb
import logfire

from src.connections.chromadb_handler import ChromaDBHandler
from src.connections.config import Config
from src.logger import Logger
from src.web_scrapper import WebScrapper

# --------------------------
# DESC: Logger

logger = Logger().get_logger()
# --------------------------


def connect_to_chroma() -> chromadb.HttpClient:
    config = Config()
    client = ChromaDBHandler().connect(config=config)
    return client


def chroma_connection_validate(*, client):
    return client.heartbeat() is not None


def execute_webscrapper():
    number = os.environ.get('JOURNAL_NUMBER', '')
    year = os.environ.get('JOURNAL_YEAR', '')

    WebScrapper().execute(number=number, year=year)


def main():
    # ------------------------------
    # DESC: conectar ao Chroma
    client = connect_to_chroma()
    # ------------------------------

    # ------------------------------
    # DESC: teste se foi possível se conectar no ChromaDB
    if not chroma_connection_validate(client=client):
        logger.info('-' * 10)
        logger.info('Error to connect to ChromaDB!')
        logger.info('-' * 10)
        logfire.exception('Error to connect to ChromaDB!')
        raise
    # ------------------------------

    # ------------------------------
    # DESC: conectar ao Chroma
    execute_webscrapper()
    # ------------------------------


if __name__ == '__main__':
    main()
