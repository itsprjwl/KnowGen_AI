from pypdf import PdfReader
from langchain_core.documents import Document

def load_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)

    documents = []

    for page_num, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()

        if page_text:
            documents.append(
                Document(
                    page_content=page_text,
                    metadata={
                        "page": page_num
                    }
                )
            )

    return documents

