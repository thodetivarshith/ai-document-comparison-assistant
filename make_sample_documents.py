"""Generate two sample PDFs (needs reportlab: pip install -r requirements-dev.txt)."""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

OUT = Path(__file__).parent / "sample_documents"

DOC_A = [
    ("Python Programming Course Syllabus (Version 1)", None),
    ("Duration", "The course runs for 8 weeks starting on 3 March 2025."),
    ("Fee", "The course fee is $400, payable before the first class."),
    ("Eligibility", "Students must have completed Introduction to Computing."),
    ("Assessment", "Assessment consists of weekly quizzes (30%) and a final exam (70%)."),
    ("Attendance", "A minimum of 75% attendance is required."),
    ("Instructor", "The course is taught by Dr. Sarah Khan."),
    ("Topics", "Variables, loops, functions, file handling and basic data structures."),
]
DOC_B = [
    ("Python Programming Course Syllabus (Version 2)", None),
    ("Duration", "The course runs for 10 weeks starting on 14 April 2025."),
    ("Fee", "The course fee is $450, payable before the first class."),
    ("Eligibility", "Students must have completed Introduction to Computing."),
    ("Assessment", "Assessment consists of weekly quizzes (20%), a capstone project (30%) and a final exam (50%)."),
    ("Attendance", "A minimum of 75% attendance is required."),
    ("Instructor", "The course is taught by Dr. Sarah Khan and Mr. Ali Raza."),
    ("Topics", "Variables, loops, functions, file handling, basic data structures and an introduction to APIs."),
]


def build(path: Path, rows) -> None:
    styles = getSampleStyleSheet()
    story = []
    for head, body in rows:
        if body is None:
            story += [Paragraph(head, styles["Title"]), Spacer(1, 12)]
        else:
            story += [Paragraph(head, styles["Heading3"]), Paragraph(body, styles["BodyText"]), Spacer(1, 6)]
    SimpleDocTemplate(str(path), pagesize=A4).build(story)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    build(OUT / "document_a.pdf", DOC_A)
    build(OUT / "document_b.pdf", DOC_B)
    print("Sample PDFs written to", OUT)
