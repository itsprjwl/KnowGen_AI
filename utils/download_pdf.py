import os

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate

from utils.config import SUMMARY_OUTPUT_PATH


def create_pdf(text):
    os.makedirs(SUMMARY_OUTPUT_PATH.parent, exist_ok=True)

    doc = SimpleDocTemplate(str(SUMMARY_OUTPUT_PATH))
    styles = getSampleStyleSheet()
    story = [Paragraph(text or "No content generated.", styles["BodyText"])]

    doc.build(story)

    return str(SUMMARY_OUTPUT_PATH)