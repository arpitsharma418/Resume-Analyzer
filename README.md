# Resume-Analyzer With AI

A tool that helps HR find the best condidates. It reads many resumes and compare each one with a job description and lists the condidates according to their score.

## How It Works:
1. Paste the job description into `job_description.txt`.
2. Put the resumes (PDF or docx) in the `resumes` folder.
3. Run the tool. It reads every resume, the AI compares it with the job description, and the   candidates are printed from best to worst.
The full results are also saved in `results.json`.

## Setup

Install the libraries:

```
groq>=1.7.0
pydantic>=2.14.3
pypdf>=7.1.0
python-docx>=1.2.0
python-dotenv>=1.2.4
```

Create a `.env` file with your Groq API key:
```
GROQ_API_KEY=your_key_here
```

Run the tool:
```
python resume_analyzer.py
```

## Tech stack
Python, Groq API, Pydantic