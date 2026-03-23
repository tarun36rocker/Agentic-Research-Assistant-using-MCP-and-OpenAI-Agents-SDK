from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os
import re

from utils.content_utils import normalize_report_content

def generate_pdf(content, topic):
    data = normalize_report_content(content)

    safe_topic = re.sub(r"[^a-zA-Z0-9._-]+", "_", topic).strip("_") or "report"

    path = f"outputs/reports/{safe_topic}.pdf"
    os.makedirs(os.path.dirname(path), exist_ok=True)

    doc = SimpleDocTemplate(path)
    styles = getSampleStyleSheet()

    story = []

    # Title
    story.append(Paragraph(f"<b>{data['title']}</b>", styles["Title"]))
    story.append(Spacer(1, 20))

    for section in data["sections"]:
        story.append(Paragraph(f"<b>{section['heading']}</b>", styles["Heading2"]))
        story.append(Spacer(1, 10))

        story.append(Paragraph(section["content"], styles["Normal"]))
        story.append(Spacer(1, 10))

        for bullet in section.get("bullets", []):
            story.append(Paragraph(f"• {bullet}", styles["Normal"]))

        story.append(Spacer(1, 20))

    doc.build(story)
    return path