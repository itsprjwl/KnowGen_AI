import os

from langchain_community.vectorstores import FAISS

from utils.config import VECTOR_STORE_DIR


def create_vector_store(documents, embeddings):
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

    vector_store = FAISS.from_documents(
        documents=documents,
        embedding=embeddings
    )

    vector_store.save_local(str(VECTOR_STORE_DIR))

    return vector_store