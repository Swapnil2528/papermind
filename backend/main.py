import re

import fitz  # PyMuPDF
from fastapi import FastAPI, UploadFile, File

app = FastAPI()


def split_questions(text):
    # 1. सगळ्या ओळी आणि जास्तीच्या जागा एकाच ओळीत आणा
    text = re.sub(r"\s+", " ", text)

    # 2. "Q3)" किंवा "a) " असे सगळे ठिकाणं शोधा
    pattern = re.compile(r"Q(\d+)\)|\b([a-c])\)\s")
    matches = list(pattern.finditer(text))

    questions = []
    current_q = None

    for i, m in enumerate(matches):
        # या खुणेपासून पुढच्या खुणेपर्यंतचा भाग
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)

        if m.group(1):
            # हे "Q3)" सारखं आहे, म्हणून मोठा प्रश्न क्रमांक लक्षात ठेवा
            current_q = m.group(1)
        else:
            # हे "a)" सारखं आहे, म्हणून हा एक छोटा प्रश्न आहे
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