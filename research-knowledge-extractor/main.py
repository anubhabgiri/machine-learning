from chunking import chunk_text
from retriever import Retriever
from app import app, QAState
import pdfplumber


import os

# ... imports ...

def extract_text_from_pdf(pdf_path):
    all_text = ""
    # Open the PDF file using a context manager
    with pdfplumber.open(pdf_path) as pdf:
        # Iterate over all pages in the document
        for page in pdf.pages:
            # Extract text from the current page
            text = page.extract_text()
            if text:
                all_text += text + "\n" # Add a newline between pages
    return all_text


# Load paper text
base_dir = os.path.dirname(os.path.abspath(__file__))

# Specify the file name here
paper_path = os.path.join(base_dir, "paper.pdf")
paper = extract_text_from_pdf(paper_path)

chunks = chunk_text(paper)

# Inject retriever
app.config = {
    "retriever": Retriever(chunks)
}

state = QAState(
    question="""You are an expert and veteran in scientific research and machine learning. 
                Can you extract the method section from this paper?
                Limit the output to 500 words
                """
)

result = app.invoke(state)
print(result["final_answer"], result["confidence"])
