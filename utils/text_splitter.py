from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_text(pdf_text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    if isinstance(pdf_text, list):
        pdf_text = "\n".join([str(t) for t in pdf_text])

    # Plain text se Document objects bana kar return karega
    chunks = text_splitter.create_documents([str(pdf_text)])
    
    return chunks