from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()


def create_rag_chain(vector_store):

    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY")
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

