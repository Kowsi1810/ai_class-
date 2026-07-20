"""
ingest.py

Reads all resumes, splits them into chunks,
creates embeddings, and stores them in ChromaDB.
"""

import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from config import (
    RESUME_FOLDER,
    CHROMA_DB_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL
)

# ---------------------------------------
# Load Embedding Model
# ---------------------------------------

embedding_model = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL
)

documents = []

print("=" * 60)
print("Resume Folder :", RESUME_FOLDER)
print("Database Path :", CHROMA_DB_PATH)
print("Collection    :", COLLECTION_NAME)
print("=" * 60)

# ---------------------------------------
# Load PDF Resumes
# ---------------------------------------

for file in os.listdir(RESUME_FOLDER):

    if file.lower().endswith(".pdf"):

        pdf_path = os.path.join(RESUME_FOLDER, file)

        print(f"Loading : {file}")

        loader = PyPDFLoader(pdf_path)

        docs = loader.load()

        for doc in docs:
            doc.metadata["filename"] = file

        documents.extend(docs)

print(f"\nLoaded {len(documents)} pages")

# ---------------------------------------
# Split Documents
# ---------------------------------------

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)

chunks = text_splitter.split_documents(documents)

print(f"Created {len(chunks)} chunks")

# ---------------------------------------
# Delete Old Collection (Optional)
# ---------------------------------------

try:

    old_db = Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embedding_model,
        collection_name=COLLECTION_NAME
    )

    old_db.delete_collection()

    print("Old Collection Deleted")

except Exception as e:

    print("No Existing Collection Found")

# ---------------------------------------
# Create New Collection
# ---------------------------------------

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embedding_model,
    persist_directory=CHROMA_DB_PATH,
    collection_name=COLLECTION_NAME
)

print("\nVector Database Created Successfully!")

print("Stored Documents :", vectorstore._collection.count())

print("=" * 60)