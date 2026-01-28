from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

md_path = Path("results/today_forecast_eval/forecast_engine_analysis.md")
out_path = Path("results/today_forecast_eval/forecast_engine_analysis.pdf")

if not md_path.exists():
    print("Markdown report not found:", md_path)
    raise SystemExit(1)

text = md_path.read_text(encoding="utf-8")

# Very small markdown -> plain conversion: preserve paragraphs and simple lists
parts = []
for block in text.split('\n\n'):
    p = block.strip()
    if not p:
        continue
    # remove code fences and inline backticks
    p = p.replace('```', '')
    p = p.replace('`', '')
    lines = [ln.rstrip() for ln in p.splitlines() if ln.strip()]
    if all(ln.lstrip().startswith('- ') for ln in lines):
        # bullet list
        for ln in lines:
            parts.append('• ' + ln.lstrip()[2:])
    else:
        # headers: remove leading # and keep text
        if lines and lines[0].lstrip().startswith('#'):
            lines[0] = lines[0].lstrip('#').strip()
        parts.append(' '.join(lines))

styles = getSampleStyleSheet()
doc = SimpleDocTemplate(str(out_path), pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
story = []
for p in parts:
    story.append(Paragraph(p.replace('\n','<br/>'), styles['BodyText']))
    story.append(Spacer(1, 6))

doc.build(story)
print('Wrote PDF to', out_path)
