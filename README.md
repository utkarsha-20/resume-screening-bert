# Resume Screening with BERT

An automated resume screening tool that ranks resumes against job descriptions using semantic similarity (BERT) and skill matching.

---

## How It Works

For each resume + job description pair, the tool computes:

- **Semantic Score** — cosine similarity between BERT embeddings of the resume and JD
- **Skill Match Score** — percentage of JD skills found in the resume
- **Years of Experience** — extracted from date ranges in the resume
- **Final Score** — weighted combination: `Semantic (75%) + Skill Match (25%)`

Results are saved to an Excel file ranked by Final Score per JD.

---

## Project Structure

```
resume-screening-bert/
├── main.py               # Entry point
├── src/
│   ├── parser.py         # Extracts text from PDF, DOCX, TXT
│   ├── skills.py         # Skills database + extraction
│   ├── scorer.py         # BERT similarity + skill match scoring
│   └── experience.py     # Years of experience extraction
├── resumes/              # Place resume files here (PDF, DOCX, TXT)
├── jds/                  # Place job description files here (TXT)
├── output/               # Results saved here as Excel
└── requirements.txt
```

---

## Setup

```bash
# Clone the repo
git clone https://github.com/your-username/resume-screening-bert.git
cd resume-screening-bert

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

# Install dependencies
pip install pandas openpyxl pdfplumber python-docx sentence-transformers scikit-learn
```

---

## Usage

1. Add resumes (PDF, DOCX, or TXT) to the `resumes/` folder
2. Add job descriptions (TXT) to the `jds/` folder
3. Run:

```bash
python main.py
```

4. Open `output/resume_screening_results.xlsx` to see ranked results

---

## Output Columns

| Column | Description |
|---|---|
| Job Description | JD filename |
| Resume | Resume filename |
| Semantic Score (%) | BERT cosine similarity score |
| Skill Match Score (%) | % of JD skills found in resume |
| Final Score (%) | Weighted final ranking score |
| JD Skills | Skills extracted from the JD |
| Resume Skills | Skills extracted from the resume |
| Matched Skills | Skills present in both |
| Years of Experience | Total experience parsed from resume |

---

## Model

Uses [`all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) from Sentence Transformers — a lightweight, fast BERT model optimized for semantic similarity.

---

## Supported File Formats

| Format | Resumes | Job Descriptions |
|---|---|---|
| PDF | Yes | — |
| DOCX | Yes | — |
| TXT | Yes | Yes |
