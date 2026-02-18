import hashlib
import re
from difflib import SequenceMatcher
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract


# ==========================
# HASHING
# ==========================

def compute_sha256(file_path: str) -> str:
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha.update(chunk)
    return sha.hexdigest()
# ==========================

def generate_certificate_pdf(student, certificate, output_path: str) -> None:
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2, height - 100, "University Certificate")

    c.setFont("Helvetica", 14)
    c.drawString(100, height - 160, f"Name: {student.full_name}")
    c.drawString(100, height - 190, f"Matric Number: {student.matric_number}")
    c.drawString(100, height - 220, f"Department: {student.department}")
    c.drawString(100, height - 250, f"Degree: {certificate.degree_title}")
    c.drawString(100, height - 280, f"Class: {certificate.degree_class}")
    c.drawString(100, height - 310, f"GPA: {certificate.gpa}")
    c.drawString(100, height - 340, f"Graduation Year: {certificate.graduation_year}")
    c.drawString(100, height - 370, f"Date Issued: {certificate.date_issued.strftime('%Y-%m-%d')}")
    c.drawString(100, height - 410, f"Certificate ID: CERT-{certificate.id}")

    c.save()


# ==========================
# TEXT EXTRACTION
# ==========================

def extract_text(file_path: str) -> str:
    if file_path.lower().endswith(".pdf"):
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    else:
        img = Image.open(file_path)
        return pytesseract.image_to_string(img)
# PARSING ENGINE
# ==========================

def parse_certificate_text(raw_text: str) -> dict:
    text = raw_text.replace("\n", " ")

    parsed = {}

    name_match = re.search(r"Name:\s*([A-Za-z\s]+)", text)
    matric_match = re.search(r"Matric Number:\s*([A-Za-z0-9\/\-]+)", text)
    year_match = re.search(r"Graduation Year:\s*(\d{4})", text)
    cert_match = re.search(r"CERT-(\d+)", text)

    if name_match:
        parsed["name"] = name_match.group(1).strip()

    if matric_match:
        parsed["matric_number"] = matric_match.group(1).strip()

    if year_match:
        parsed["graduation_year"] = int(year_match.group(1))

    if cert_match:
        parsed["certificate_id"] = int(cert_match.group(1))

    return parsed


# ==========================
# STRING SIMILARITY
# ==========================

def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()
