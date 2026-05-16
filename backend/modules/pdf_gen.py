"""
modules/pdf_gen.py
Clean PDF generator matching original resume format exactly.
"""

import os, shutil
from typing import Dict, Any, List

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer,
        HRFlowable, Table, TableStyle
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
    _RL = True
except ImportError:
    _RL = False


def safe(text: str) -> str:
    if not text: return ""
    return (str(text).strip()
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


class PDFGenerator:

    def generate(self, parsed: Dict[str, Any], out_path: str) -> str:
        if _RL:
            self._rl(parsed, out_path)
        else:
            self._txt(parsed, out_path)
        return out_path

    def _rl(self, p: Dict[str, Any], out: str):
        doc = SimpleDocTemplate(
            out, pagesize=A4,
            leftMargin=1.8*cm, rightMargin=1.8*cm,
            topMargin=1.5*cm,  bottomMargin=1.5*cm,
        )

        # ── Styles ────────────────────────────────────────────────────────
        def style(name, **kwargs):
            defaults = dict(fontName="Helvetica", fontSize=10,
                            textColor=colors.black, leading=14)
            defaults.update(kwargs)
            return ParagraphStyle(name, **defaults)

        s_name    = style("N", fontName="Helvetica-Bold", fontSize=18,
                          alignment=TA_CENTER, spaceAfter=2)
        s_contact = style("C", fontSize=9, alignment=TA_CENTER,
                          spaceAfter=2, textColor=colors.HexColor("#333333"))
        s_section = style("S", fontName="Helvetica-Bold", fontSize=10.5,
                          spaceBefore=10, spaceAfter=1)
        s_bold    = style("B", fontName="Helvetica-Bold", fontSize=9.5,
                          spaceAfter=1)
        s_italic  = style("I", fontName="Helvetica-Oblique", fontSize=9,
                          spaceAfter=2, textColor=colors.HexColor("#444"))
        s_body    = style("T", fontSize=9.5, spaceAfter=2,
                          alignment=TA_JUSTIFY)
        s_bullet  = style("L", fontSize=9.5, leftIndent=10, spaceAfter=1)
        s_right   = style("R", fontSize=9, alignment=TA_RIGHT)

        def hr():
            return HRFlowable(width="100%", thickness=0.7,
                               color=colors.black, spaceAfter=4, spaceBefore=1)

        def section(title):
            return [Paragraph(safe(title), s_section), hr()]

        def two_col(left_text, right_text, left_style, right_style, ratio="75%"):
            """Create a two-column row."""
            lw = float(ratio.strip("%")) / 100
            rw = 1 - lw
            page_w = A4[0] - 3.6*cm
            t = Table(
                [[Paragraph(left_text, left_style),
                  Paragraph(right_text, right_style)]],
                colWidths=[page_w * lw, page_w * rw]
            )
            t.setStyle(TableStyle([
                ("VALIGN",       (0,0), (-1,-1), "TOP"),
                ("LEFTPADDING",  (0,0), (-1,-1), 0),
                ("RIGHTPADDING", (0,0), (-1,-1), 0),
                ("TOPPADDING",   (0,0), (-1,-1), 0),
                ("BOTTOMPADDING",(0,0), (-1,-1), 2),
            ]))
            return t

        story = []

        # ── Name ──────────────────────────────────────────────────────────
        name = safe(p.get("name", ""))
        if name:
            story.append(Paragraph(name, s_name))

        # ── Sub-header: degree + university (if available) ────────────────
        edu = p.get("education", [])
        if edu:
            first_edu = edu[0]
            deg  = safe(first_edu.get("degree", ""))
            inst = safe(first_edu.get("institution", ""))
            if deg or inst:
                sub = ", ".join(filter(None, [deg, inst]))
                story.append(Paragraph(sub, s_contact))

        # ── Contact line ──────────────────────────────────────────────────
        parts = list(filter(None, [
            safe(p.get("email", "")),
            safe(p.get("linkedin", "")),
            safe(p.get("github", "")),
            safe(p.get("phone", "")),
        ]))
        if parts:
            story.append(Paragraph("    ".join(parts), s_contact))

        story.append(Spacer(1, 6))

        # ── Summary ───────────────────────────────────────────────────────
        summary = p.get("summary", "").strip()
        if summary:
            story.extend(section("Summary"))
            story.append(Paragraph(safe(summary), s_body))

        # ── Education ─────────────────────────────────────────────────────
        if edu:
            story.extend(section("Education"))
            for e in edu:
                inst = safe(e.get("institution", ""))
                deg  = safe(e.get("degree", ""))
                yr   = safe(e.get("year", ""))
                gpa  = safe(e.get("gpa", ""))

                if inst and yr:
                    story.append(two_col(
                        f"<b>{inst}</b>", yr,
                        s_bold, s_right
                    ))
                elif inst:
                    story.append(Paragraph(f"<b>{inst}</b>", s_bold))

                if deg:
                    story.append(Paragraph(deg, s_body))
                if gpa:
                    story.append(Paragraph(f"Percentage: {gpa}%", s_italic))
                story.append(Spacer(1, 3))

        # ── Projects ──────────────────────────────────────────────────────
        proj_list = p.get("projects", [])
        if proj_list:
            story.extend(section("Projects"))
            for pr in proj_list:
                title = safe(pr.get("title", ""))
                links = pr.get("links", [])
                link_label = ""
                if links:
                    # Show just domain/path of link
                    lnk = links[0]
                    if "github" in lnk.lower():
                        link_label = "GitHub"
                    else:
                        link_label = lnk.split("/")[-1][:20]

                if title:
                    if link_label:
                        story.append(two_col(
                            f"<b>{title}</b>",
                            f'<font color="#4361ee">{safe(link_label)}</font>',
                            s_bold, s_right
                        ))
                    else:
                        story.append(Paragraph(f"<b>{title}</b>", s_bold))

                for desc in pr.get("description", []):
                    d = safe(desc)
                    if d:
                        story.append(Paragraph(f"• {d}", s_bullet))

                story.append(Spacer(1, 4))

        # ── Skills ────────────────────────────────────────────────────────
        skills = p.get("skills", [])
        if skills:
            story.extend(section("Skills"))
            skills_text = ", ".join(safe(s) for s in sorted(set(skills)))
            story.append(Paragraph(skills_text, s_body))

        # ── Experience ────────────────────────────────────────────────────
        exp_list = p.get("experience", [])
        if exp_list:
            story.extend(section("Leadership & Experience"))
            for entry in exp_list:
                title    = safe(entry.get("title", ""))
                company  = safe(entry.get("company", ""))
                duration = safe(entry.get("duration", ""))

                full_title = title
                if company:
                    full_title += f", {company}"

                if full_title and duration:
                    story.append(two_col(
                        f"<b>{full_title}</b>", duration,
                        s_bold, s_right
                    ))
                elif full_title:
                    story.append(Paragraph(f"<b>{full_title}</b>", s_bold))

                for bullet in entry.get("bullets", []):
                    b = safe(bullet)
                    if b:
                        story.append(Paragraph(f"• {b}", s_bullet))

                story.append(Spacer(1, 4))

        # ── Certifications ────────────────────────────────────────────────
        certs = p.get("certifications", [])
        if certs:
            story.extend(section("Certifications"))
            for c in certs:
                if c.strip():
                    story.append(Paragraph(f"• {safe(c)}", s_bullet))

        # ── Achievements ──────────────────────────────────────────────────
        ach = p.get("achievements", [])
        if ach:
            story.extend(section("Achievements"))
            for a in ach:
                if a.strip():
                    story.append(Paragraph(f"• {safe(a)}", s_bullet))

        doc.build(story)

    def _txt(self, p: Dict[str, Any], out: str):
        lines = [p.get("name","")]
        lines.append("  ".join(filter(None,[p.get("email"),p.get("phone"),p.get("linkedin"),p.get("github")])))
        def sec(t): lines.extend(["",t,"─"*50])
        if p.get("summary"):    sec("Summary");    lines.append(p["summary"])
        if p.get("education"):  sec("Education")
        for e in p.get("education",[]): lines.append(f"{e.get('institution','')} {e.get('year','')}")
        if p.get("projects"):   sec("Projects")
        for pr in p.get("projects",[]): [lines.append(f"• {d}") for d in pr.get("description",[])]
        if p.get("skills"):     sec("Skills");     lines.append(", ".join(p["skills"]))
        if p.get("experience"): sec("Experience")
        for e in p.get("experience",[]): [lines.append(f"• {b}") for b in e.get("bullets",[])]
        txt = out.replace(".pdf",".txt")
        with open(txt,"w",encoding="utf-8") as f: f.write("\n".join(lines))
        shutil.copy(txt, out)
