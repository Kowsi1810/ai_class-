"""
vector_store.py
"""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from config import (
    CHROMA_DB_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    TOP_K,
)


class ResumeVectorStore:

    def __init__(self):

        self.embedding_model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL
        )

        self.vector_db = Chroma(
            persist_directory=CHROMA_DB_PATH,
            embedding_function=self.embedding_model,
            collection_name=COLLECTION_NAME
        )

        print("=" * 50)
        print("Connected to ChromaDB")
        print("Collection :", COLLECTION_NAME)
        print("Documents  :", self.vector_db._collection.count())
        print("=" * 50)

    def similarity_search(self, query, k=None):

        return self.vector_db.similarity_search(
            query,
            k=k or TOP_K
        )

    def similarity_search_with_score(self, query, k=None):

        return self.vector_db.similarity_search_with_score(
            query,
            k=k or TOP_K
        )

    def get_collection(self):

        return self.vector_db