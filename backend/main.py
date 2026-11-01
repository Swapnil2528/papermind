import re

import fitz  # PyMuPDF
from fastapi import FastAPI, UploadFile, File

app = FastAPI()


def split_questions(text):

    text = re.sub(r"\s+", " ", text)

    
    pattern = re.compile(r"Q(\d+)\)|\b([a-c])\)\s")
    matches = list(pattern.finditer(text))

    questions = []
    current_q = None

    for i, m in enumerate(matches):
    
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)

        if m.group(1):
        
            current_q = m.group(1)
        else:
            
            body = text[m.end():end].strip()
            questions.append(
                {
                    "question_no": "Q" + current_q,
                    "part": m.group(2),
                    "text": body,
                }
            )

    return questions


@app.get("/")
def home():
    return {"message": "PaperMind is running!"}


@app.post("/upload")
async def upload_paper(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    text = ""
    for page in doc:
        text += page.get_text()

    questions = split_questions(text)

    return {
        "filename": file.filename,
        "pages": len(doc),
        "characters": len(text),
        "total_questions": len(questions),
        "questions": questions,
    }
