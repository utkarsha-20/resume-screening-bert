import pdfplumber
import docx


def read_pdf(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception:
        pass
    return text


def read_docx(file_path):
    try:
        document = docx.Document(file_path)
        return "\n".join([p.text for p in document.paragraphs])
    except Exception:
        return ""


def read_txt(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def extract_text(file_path):
    lower = file_path.lower()

    if lower.endswith(".pdf"):
        return read_pdf(file_path)

    if lower.endswith(".docx"):
        return read_docx(file_path)

    if lower.endswith(".txt"):
        return read_txt(file_path)

    return ""
