from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
import io
import re
import sqlite3
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "https://ai-resume-analyzer-woad-zeta.vercel.app"
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "analyzer.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            email TEXT,
            phone TEXT,
            skills TEXT,
            score INTEGER,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


SKILLS = [
    "Python", "Java", "C", "C++", "SQL", "HTML", "CSS", "JavaScript",
    "React", "Node.js", "FastAPI", "Django", "Spring Boot",
    "Machine Learning", "Deep Learning", "Artificial Intelligence",
    "TensorFlow", "PyTorch", "OpenCV", "Pandas", "NumPy",
    "Scikit-learn", "Git", "GitHub", "Docker", "AWS",
    "MongoDB", "MySQL", "PostgreSQL"
]


@app.get("/")
def home():
    return {"message": "AI Resume Analyzer Backend is running!"}


@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):

    contents = await file.read()
    reader = PdfReader(io.BytesIO(contents))

    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    email_match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )
    email = email_match.group(0) if email_match else "Not found"

    phone_match = re.search(
        r"(?:\+91[\s-]?)?[6-9]\d{9}",
        text
    )
    phone = phone_match.group(0) if phone_match else "Not found"

    found_skills = []
    text_lower = text.lower()

    for skill in SKILLS:
        skill_lower = skill.lower()
        pattern = r'(?<![a-zA-Z0-9])' + re.escape(skill_lower) + r'(?![a-zA-Z0-9])'
        if re.search(pattern, text_lower):
            found_skills.append(skill)

    score = calculate_resume_score(text, email, phone, found_skills)

    # --- SAVE TO DATABASE ---
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO analyses (filename, email, phone, skills, score, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (
            file.filename,
            email,
            phone,
            ", ".join(found_skills),
            score["total_score"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )
    conn.commit()
    conn.close()

    return {
        "filename": file.filename,
        "email": email,
        "phone": phone,
        "skills": found_skills,
        "score": score["total_score"],
        "breakdown": score["breakdown"],
        "text": text
    }


@app.get("/admin/dashboard")
def get_dashboard():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, filename, email, phone, skills, score, timestamp FROM analyses ORDER BY id DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "filename": row[1],
            "email": row[2],
            "phone": row[3],
            "skills": row[4],
            "score": row[5],
            "timestamp": row[6]
        })

    return {"total_uploads": len(results), "records": results}


def count_stem_occurrences(text_lower, stems):
    total = 0
    for stem in stems:
        matches = re.findall(r'\b' + re.escape(stem) + r'\w*\b', text_lower)
        total += len(matches)
    return total


def calculate_resume_score(text, email, phone, skills):

    score = 0
    breakdown = {}
    text_lower = text.lower()
    word_count = len(text.split())

    contact_score = 0
    if email != "Not found":
        contact_score += 5
    if phone != "Not found":
        contact_score += 5
    breakdown["Contact Information"] = contact_score
    score += contact_score

    skill_count = len(skills)
    if skill_count >= 10:
        skills_score = 20
    elif skill_count >= 7:
        skills_score = 17
    elif skill_count >= 5:
        skills_score = 14
    elif skill_count >= 3:
        skills_score = 10
    elif skill_count >= 1:
        skills_score = 6
    else:
        skills_score = 0
    breakdown["Skills"] = skills_score
    score += skills_score

    education_keywords = [
        "bachelor", "b\\.tech", "b\\.e\\.?", "master", "m\\.tech",
        "university", "college", "cgpa", "gpa", "percentage"
    ]
    edu_matches = sum(
        1 for kw in education_keywords
        if re.search(r'\b' + kw + r'\b', text_lower)
    )
    education_score = min(edu_matches * 4, 15)
    breakdown["Education"] = education_score
    score += education_score

    project_stems = ["develop", "built", "build", "design", "implement", "creat"]
    project_matches = count_stem_occurrences(text_lower, project_stems)
    project_score = min(project_matches * 2, 15)
    breakdown["Projects"] = project_score
    score += project_score

    experience_stems = ["intern", "employ", "work experience", "worked at"]
    exp_matches = count_stem_occurrences(text_lower, experience_stems)
    has_duration = bool(re.search(r"\b20\d{2}\b", text))
    experience_score = min(exp_matches * 5, 15)
    if has_duration:
        experience_score = min(experience_score + 3, 15)
    breakdown["Experience"] = experience_score
    score += experience_score

    sections = ["education", "skills", "projects", "experience"]
    sections_found = sum(1 for s in sections if s in text_lower)
    structure_score = round((sections_found / 4) * 10)
    breakdown["Resume Structure"] = structure_score
    score += structure_score

    if word_count >= 500:
        content_score = 10
    elif word_count >= 350:
        content_score = 7
    elif word_count >= 200:
        content_score = 5
    elif word_count >= 100:
        content_score = 3
    else:
        content_score = 1
    breakdown["Content Quality"] = content_score
    score += content_score

    readability_score = 0
    if word_count >= 150:
        readability_score += 2
    if "\n" in text:
        readability_score += 1
    if re.search(r"[•\-\*]\s", text):
        readability_score += 2
    breakdown["ATS Readability"] = readability_score
    score += readability_score

    return {
        "total_score": min(score, 100),
        "breakdown": breakdown
    }