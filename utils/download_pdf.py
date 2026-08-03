from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def create_pdf(text):

    pdf_file = "AI_Summary.pdf"

    doc = SimpleDocTemplate(pdf_file)

    styles = getSampleStyleSheet()

    story = [Paragraph(text, styles["BodyText"])]

    doc.build(story)

    return pdf_file