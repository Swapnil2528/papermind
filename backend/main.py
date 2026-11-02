import re

import fitz  # PyMuPDF
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from rapidfuzz import fuzz

from database import Base, Paper, Question, SessionLocal, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SIMILARITY_LIMIT = 92


def normalize(text):
    text = text.lower()
    return re.sub(r"[^a-z0-9 ]", "", text)


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
                    "question_no": "Q" + str(current_q),
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

    db = SessionLocal()
    try:
        existing = db.query(Paper).filter(Paper.filename == file.filename).first()
        if existing:
            return {
                "message": "This paper is already uploaded",
                "paper_id": existing.id,
            }

        paper = Paper(filename=file.filename)
        db.add(paper)
        db.commit()
        db.refresh(paper)

        old_questions = (
            db.query(Question).filter(Question.paper_id != paper.id).all()
        )

        repeated_count = 0
        for q in questions:
            new_row = Question(
                paper_id=paper.id,
                question_no=q["question_no"],
                part=q["part"],
                text=q["text"],
            )
            db.add(new_row)
            db.flush()

            new_row.group_id = new_row.id

            for old in old_questions:
                score = fuzz.token_set_ratio(
                    normalize(q["text"]), normalize(old.text)
                )
                if score >= SIMILARITY_LIMIT:
                    new_row.group_id = old.group_id
                    repeated_count += 1
                    break

        db.commit()
        paper_id = paper.id
    finally:
        db.close()

    return {
        "paper_id": paper_id,
        "filename": file.filename,
        "pages": len(doc),
        "total_questions": len(questions),
        "repeated_from_earlier_papers": repeated_count,
    }


@app.get("/questions")
def list_questions():
    db = SessionLocal()
    try:
        rows = db.query(Question).all()
        return [
            {
                "id": r.id,
                "paper_id": r.paper_id,
                "question_no": r.question_no,
                "part": r.part,
                "group_id": r.group_id,
                "text": r.text,
            }
            for r in rows
        ]
    finally:
        db.close()


@app.get("/repeated")
def repeated_questions():
    db = SessionLocal()
    try:
        rows = db.query(Question).all()

        groups = {}
        for r in rows:
            groups.setdefault(r.group_id, []).append(r)

        result = []
        for group_id, items in groups.items():
            paper_ids = sorted({i.paper_id for i in items})
            if len(paper_ids) > 1:
                result.append(
                    {
                        "group_id": group_id,
                        "times_repeated": len(paper_ids),
                        "question": items[0].text,
                        "paper_ids": paper_ids,
                    }
                )

        result.sort(key=lambda x: x["times_repeated"], reverse=True)
        return result
    finally:
        db.close()