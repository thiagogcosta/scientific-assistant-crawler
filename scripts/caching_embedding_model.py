import os

from chromadb.utils import embedding_functions

embedding_model_name = os.environ.get('EMBEDDING_MODEL_NAME', '')

embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=embedding_model_name
)
