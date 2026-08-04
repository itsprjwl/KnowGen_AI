from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from utils.config import DEFAULT_GROQ_MODEL, get_api_key


def create_rag_chain(vector_store):
    api_key = get_api_key()
    llm = ChatGroq(
        model=DEFAULT_GROQ_MODEL,
        api_key=api_key
    )

    retriever = vector_store.as_retriever(
        search_kwargs={"k": 3}
    )

    prompt = ChatPromptTemplate.from_template(
        """
        Answer the question based on the context below.

        Context:
        {context}

        Question:
        {input}
        """
    )

    return llm, retriever, prompt

