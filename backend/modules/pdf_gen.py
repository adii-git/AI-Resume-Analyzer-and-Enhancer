"""
modules/pdf_gen.py
Generates a professional PDF resume with ReportLab.
Falls back to plain-text if ReportLab is not installed.
"""
import os, shutil
from typing import Dict, Any

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.lib.enums import TA_CENTER
    _RL = True
except ImportError:
    _RL = False


class PDFGenerator:
    def generate(self, parsed: Dict[str, Any], out_path: str) -> str:
        if _RL:
            self._rl(parsed, out_path)
        else:
            self._txt(parsed, out_path)
        return out_path

    def _rl(self, p: Dict[str, Any], out: str):
        doc    = SimpleDocTemplate(out, pagesize=A4,
                                   leftMargin=20*mm, rightMargin=20*mm,
                                   topMargin=15*mm, bottomMargin=15*mm)
        styles = getSampleStyleSheet()
        s_name = ParagraphStyle("N", parent=styles["Title"], fontSize=22,
                                textColor=colors.HexColor("#1a1a2e"), spaceAfter=2)
        s_con  = ParagraphStyle("C", parent=styles["Normal"], fontSize=9,
                                textColor=colors.HexColor("#555"), alignment=TA_CENTER, spaceAfter=6)
        s_hdr  = ParagraphStyle("H", parent=styles["Heading2"], fontSize=11,
                                textColor=colors.HexColor("#16213e"), spaceBefore=8, spaceAfter=2)
        s_body = ParagraphStyle("B", parent=styles["Normal"], fontSize=9.5, leading=14, spaceAfter=3)
        s_bul  = ParagraphStyle("L", parent=styles["Normal"], fontSize=9, leading=13, leftIndent=10, spaceAfter=2)
        s_job  = ParagraphStyle("J", parent=styles["Normal"], fontSize=10, spaceAfter=1)

        def hr():
            return HRFlowable(width="100%", thickness=0.5,
                               color=colors.HexColor("#4361ee"), spaceAfter=4)
        def sec(title):
            story.append(Spacer(1, 4))
            story.append(Paragraph(title.upper(), s_hdr))
            story.append(hr())

        story = []
        story.append(Paragraph(p.get("name","Your Name"), s_name))
        parts = [x for x in [p.get("email"),p.get("phone"),p.get("linkedin"),p.get("github")] if x]
        story.append(Paragraph(" | ".join(parts), s_con))
        story.append(Spacer(1,4))

        if p.get("summary"):
            sec("Professional Summary")
            story.append(Paragraph(p["summary"], s_body))

        if p.get("skills"):
            sec("Skills")
            story.append(Paragraph(", ".join(p["skills"]), s_body))

        if p.get("experience"):
            sec("Professional Experience")
            for e in p["experience"]:
                line = f"<b>{e.get('title','')}</b>"
                if e.get("company"):  line += f" — {e['company']}"
                if e.get("duration"): line += f" &nbsp;<i><font size='8'>{e['duration']}</font></i>"
                story.append(Paragraph(line, s_job))
                for b in e.get("bullets",[]): story.append(Paragraph(f"• {b}", s_bul))
                story.append(Spacer(1,3))

        if p.get("education"):
            sec("Education")
            for e in p["education"]:
                line = f"<b>{e.get('degree','')}</b>"
                if e.get("institution"): line += f" — {e['institution']}"
                if e.get("year"):        line += f" ({e['year']})"
                if e.get("gpa"):         line += f" | GPA: {e['gpa']}"
                story.append(Paragraph(line, s_body))

        if p.get("projects"):
            sec("Projects")
            for pr in p["projects"]:
                ts   = ", ".join(pr.get("tech_stack",[])[:5])
                line = f"<b>{pr.get('title','')}</b>"
                if ts: line += f" <font size='8'>({ts})</font>"
                story.append(Paragraph(line, s_job))
                for d in pr.get("description",[]): story.append(Paragraph(f"• {d}", s_bul))
                if pr.get("links"): story.append(Paragraph(f"<font size='8' color='#4361ee'>{pr['links'][0]}</font>", s_bul))
                story.append(Spacer(1,3))

        for key, title in [("certifications","Certifications"),("achievements","Achievements")]:
            items = p.get(key,[])
            if items:
                sec(title)
                for item in items: story.append(Paragraph(f"• {item}", s_bul))

        doc.build(story)

    def _txt(self, p: Dict[str, Any], out: str):
        lines = [p.get("name",""), " | ".join(filter(None,[p.get("email"),p.get("phone"),p.get("linkedin"),p.get("github")]))]
        def sec(t): lines.extend(["",t.upper(),"─"*len(t)])
        if p.get("summary"):    sec("Summary");       lines.append(p["summary"])
        if p.get("skills"):     sec("Skills");        lines.append(", ".join(p["skills"]))
        for e in p.get("experience",[]):
            sec(f"{e.get('title','')} — {e.get('company','')}  {e.get('duration','')}")
            for b in e.get("bullets",[]): lines.append(f"  • {b}")
        for e in p.get("education",[]):
            sec(f"{e.get('degree','')} — {e.get('institution','')} {e.get('year','')}")
        for pr in p.get("projects",[]):
            sec(f"Project: {pr.get('title','')}")
            for d in pr.get("description",[]): lines.append(f"  • {d}")
        txt = out.replace(".pdf",".txt")
        with open(txt,"w",encoding="utf-8") as f: f.write("\n".join(lines))
        shutil.copy(txt, out)
