import json
import os
from pathlib import Path

from docx import Document
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field
from pypdf import PdfReader

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"
job_file = Path("job_description.txt")
resume_folder = Path("resumes")
output_file = Path("result.json")

# this system prompt gives the ai its role
SYSTEM_PROMPT = """You are an experienced HR recruiter.
Compare a resume with a job description. Look at skills, experience, education and the overall fit.
Be strict and fair. Do not give a high score if important requirements are missing.

Return only JSON with exactly these keys:
- score: a number between 0 and 100, representing how well the resume matches the job description
- name: full name of the candidate
- email: email address
- phone: phone number
- total_experience_years: total years of work experience as a number, for example 2.5
- skills: list of all skills mentioned in the resume
- experiences: list of jobs, and each job has these keys:
    company, role, duration, description, skills_used (list of strings)
- education: list of strings, one per degree, with the college name and year if available
- projects: list of strings, one per project, with a short description
- certifications: list of certification names

Rules:
- Use only the information written in the resume. Do not guess or invent anything.
- If a single value is missing, use null. If a list is empty, use [].
- Count work experience from jobs and internships only. Do not count study years.
"""

# User Prompt: it carries data and changes for every resume
user_prompt = """JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}
"""

# output format for every match
class Experience(BaseModel):
      company: str | None = None
      role: str | None = None
      duration: str | None = None
      description: str | None = None
      skills_used: list[str] = []

class ResumeResult(BaseModel):
      score: int | None = None
      name: str | None = None
      email: str | None = None
      phone: str | None = None
      total_experience_years: float | None = None
      skills: list[str] = []
      experiences: list[Experience] = []
      education: list[str] = []
      projects: list[str] = []
      certifications: list[str] = []
      file_name: str | None = None

# read the pdf and docx file
def read_resume(path: Path) -> str:
      extension = path.suffix.lower()

      if extension == ".pdf":
            reader = PdfReader(path)
            pages = [page.extract_text() or "" for page in reader.pages]

            return "\n".join(pages)

      if extension == ".docx":
            document = Document(path)

            lines = [paragraph.text for paragraph in document.paragraphs]

            for table in document.tables:
                  for row in table.rows:
                        lines.append(" | ".join(cell.text for cell in row.cells))

            return "\n".join(lines)
      
      raise ValueError(f"Unsupported file type: {extension}")

# Analyze resume text with job description
def analyze_resume(job_description: str, resume_text: str) -> ResumeResult:
      prompt = user_prompt.format(job_description=job_description, resume_text=resume_text)

      response = client.chat.completions.create(
            model = MODEL,
            messages = [
                  {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                  },
                  {
                        "role": "user",
                        "content": prompt
                  }
            ],
            response_format={"type": "json_object"},
            temperature=0,
      )

      json_text = response.choices[0].message.content

      return ResumeResult.model_validate_json(json_text)

def main():
      job_description = job_file.read_text(encoding="utf-8").strip()

      if not job_description:
            print("job_description.txt file is empty. Please paste the job description first.")
            return 

      resume_files = [
            f for f in resume_folder.iterdir() if f.suffix.lower() in (".pdf", ".docx")
      ]

      if not resume_files:
            print("No resume found in the resumes folder")
            return

      results = []

      for file in resume_files:
            print(f"Analyzing {file.name}")

            try:
                  text = read_resume(file)
                  result = analyze_resume(job_description, text)
                  result.file_name = file.name
                  results.append(result)
            except Exception as error:
                  print(f"Skipped {file.name}: {error}")

      results.sort(key = lambda r: r.score, reverse=True)

      print("\n ---Ranking---")

      for rank, r in enumerate(results, start=1):
            print(f"\n#{rank}  {r.name or 'Unknown'}")
            print(f"score: {r.score or 0}%")
            print(f"email: {r.email or 'Not found'}")
            print(f"phone: {r.phone or 'Not found'}")
            print(f"experience: {r.total_experience_years or 0} years")
            print(f"skills: {', '.join(r.skills)}")
            print(f"education: {', '.join(r.education)}")

      data = [r.model_dump() for r in results]
      output_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
      print(f"\n Saved result to {output_file}")