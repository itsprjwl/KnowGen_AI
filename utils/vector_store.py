from langchain_community.vectorstores import FAISS

def create_vector_store(documents, embeddings):
    vector_store = FAISS.from_documents(
        documents=documents,
        embedding=embeddings
    )

    vector_store.save_local("vectorstore")

    return vector_store