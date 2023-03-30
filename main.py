from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import requests
import xml.etree.ElementTree as ET
import pdfplumber
import io
from typing import Optional

ARXIV_API_URL = "http://export.arxiv.org/api/query"

def parse_entry(entry):
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    
    paper_id_elem = entry.find("atom:id", ns)
    paper_id = paper_id_elem.text.split('/')[-1] if paper_id_elem is not None else ""
    
    title_elem = entry.find("atom:title", ns)
    title = title_elem.text if title_elem is not None else ""
    
    authors = [
        author.find("atom:name", ns).text
        for author in entry.findall("atom:author", ns)
        if author.find("atom:name", ns) is not None
    ]
    authors_str = ", ".join(authors)
    
    abstract_elem = entry.find("atom:summary", ns)
    abstract = abstract_elem.text if abstract_elem is not None else ""
    
    pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"

    return {
        "paper_id": paper_id,
        "authors": authors_str,
        "title": title,
        "abstract": abstract,
        "pdf_url": pdf_url
    }

app = FastAPI()

# Set up CORS middleware
origins = [
    "https://chat.openai.com",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=".", html=True), name="static")

@app.get("/search")
async def search_papers(request: Request, text: Optional[str] = None):
    if text is None:
        text = request.query_params.get("text")
    payload = {"search_query": f"all:{text}", "start": 0, "max_results": 10}
    response = requests.get(ARXIV_API_URL, params=payload)

    root = ET.fromstring(response.text)

    entries = root.findall("{http://www.w3.org/2005/Atom}entry")

    results = []
    for entry in entries:
        result = parse_entry(entry)
        del result["abstract"]
        del result["pdf_url"]
        results.append(result)

    return results

@app.get("/abstract")
async def get_abstract(request: Request, paper: Optional[str] = None):
    if paper is None:
        paper = request.query_params.get("paper")
    payload = {"id_list": paper}
    response = requests.get(ARXIV_API_URL, params=payload)

    root = ET.fromstring(response.text)
    entry = root.find("{http://www.w3.org/2005/Atom}entry")
    result = parse_entry(entry)
    del result["pdf_url"]

    return result

@app.get("/full")
async def get_full_paper(request: Request, paper: Optional[str] = None):
    if paper is None:
        paper = request.query_params.get("paper")
    pdf_url = f"https://arxiv.org/pdf/{paper}.pdf"
    
    # Download the PDF file as a binary object
    response = requests.get(pdf_url)
    pdf_file = io.BytesIO(response.content)

    # Extract text from the PDF file
    with pdfplumber.open(pdf_file) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages)

    result = {
        "paper_id": paper,
        "text": text
    }
    return result

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)

if __name__ == "__main__":
    main()