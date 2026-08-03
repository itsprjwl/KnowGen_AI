from rag_chain import load_llm

llm = load_llm()

response = llm.invoke("Hello, introduce yourself")

print(response.content)