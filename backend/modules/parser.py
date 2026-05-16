"""
modules/parser.py
Resume parser - fixed text extraction to preserve spaces properly.
"""

import re, os
from typing import Dict, Any, List, Optional

try:
    import pdfplumber
    _PDF = "pdfplumber"
except ImportError:
    pdfplumber = None
    _PDF = None

try:
    from docx import Document as _DocxDoc
    _DOCX = True
except ImportError:
    _DOCX = False

try:
    import spacy
    _NLP = spacy.load("en_core_web_sm")
except Exception:
    _NLP = None

TECH_SKILLS = {
    "python","java","javascript","typescript","c++","c#","go","rust","kotlin","swift",
    "ruby","php","scala","r","matlab","bash","sql","html","css","react","angular","vue",
    "node.js","express","django","flask","fastapi","spring","next.js","graphql",
    "machine learning","deep learning","nlp","computer vision","tensorflow","pytorch",
    "keras","scikit-learn","pandas","numpy","spark","hadoop","tableau","power bi",
    "aws","azure","gcp","docker","kubernetes","terraform","ansible","ci/cd","jenkins",
    "github actions","linux","git","mysql","postgresql","mongodb","redis","elasticsearch",
    "cassandra","agile","scrum","rest api","microservices","system design","devops","mlops",
    "data structures","algorithms","oop","unit testing","figma","jira","kafka","langchain",
    "hugging face","gradio","faiss","opencv","matplotlib","seaborn","langchain",
}
SOFT_SKILLS = {
    "communication","leadership","teamwork","problem solving","critical thinking",
    "project management","time management","adaptability","creativity",
    "collaboration","mentoring","analytical","detail oriented",
}

_EMAIL    = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE    = re.compile(r"(\+?\d[\d\s\-\(\)]{7,}\d)")
_LINKEDIN = re.compile(r"linkedin\.com/in/[\w\-]+", re.I)
_GITHUB   = re.compile(r"github\.com/[\w\-]+", re.I)
_DEGREE   = re.compile(r"(b\.?tech|b\.?e|b\.?sc|b\.?a|m\.?tech|m\.?sc|m\.?s|m\.?b\.?a|ph\.?d|bachelor|master|associate|doctorate)", re.I)
_TITLE    = re.compile(r"(engineer|developer|analyst|manager|intern|scientist|architect|designer|consultant|lead|director|associate|specialist|member|coordinator)", re.I)
_GPA      = re.compile(r"(gpa|cgpa|percentage)[:\s]*([\d.]+)", re.I)
_YEAR     = re.compile(r"\b(19|20)\d{2}\b")
_DATE     = re.compile(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,]*\d{4}", re.I)
_IMPACT   = re.compile(r"(\d+%|\$[\d,]+[km]?|\d+[xX]|\d+\s*(million|billion|k\b)|\d+\s*(users|clients|requests))", re.I)
_URL      = re.compile(r"https?://\S+")
_BULLETS  = ("•", "-", "●", "▸", "∙", "*", "–", "→", "◦", "▪")

_SEC = {
    "education"     : r"(education|academic|qualification|degree)",
    "experience"    : r"(experience|employment|work history|professional|career|leadership)",
    "skills"        : r"(skills|technologies|tech stack|competencies|proficiencies|expertise)",
    "projects"      : r"(projects|portfolio|personal projects)",
    "summary"       : r"(summary|objective|profile|about|overview)",
    "certifications": r"(certification|certificate|courses|training)",
    "achievements"  : r"(achievement|award|honor|recognition)",
}


class ResumeParser:

    def parse(self, path: str) -> Dict[str, Any]:
        ext  = os.path.splitext(path)[1].lower()
        text = self._pdf(path) if ext == ".pdf" else self._docx(path)
        if not text.strip():
            raise ValueError("No text could be extracted.")
        return self._build(text)

    # ── PDF extraction using word-level grouping ──────────────────────────
    def _pdf(self, path: str) -> str:
        if pdfplumber is None:
            raise RuntimeError("pdfplumber not installed.")

        full_text = ""
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    try:
                        # Try word-level extraction first (better spacing)
                        words = page.extract_words(
                            x_tolerance=3,
                            y_tolerance=3,
                            keep_blank_chars=False,
                        )
                        if words:
                            lines_dict = {}
                            for w in words:
                                y_key = round(float(w["top"]) / 4) * 4
                                if y_key not in lines_dict:
                                    lines_dict[y_key] = []
                                lines_dict[y_key].append((float(w["x0"]), w["text"]))
                            for y in sorted(lines_dict.keys()):
                                line_words = sorted(lines_dict[y], key=lambda x: x[0])
                                line = " ".join(w[1] for w in line_words)
                                full_text += line + "\n"
                        else:
                            # Fallback to extract_text
                            t = page.extract_text()
                            if t:
                                full_text += t + "\n"
                    except Exception:
                        # Last resort fallback
                        try:
                            t = page.extract_text()
                            if t:
                                full_text += t + "\n"
                        except Exception:
                            pass

        except Exception as e:
            raise RuntimeError(f"Failed to read PDF: {e}")

        if not full_text.strip():
            raise ValueError("No text extracted. PDF may be image-based.")

        return full_text

    def _docx(self, path: str) -> str:
        if not _DOCX:
            raise RuntimeError("python-docx not installed.")
        doc   = _DocxDoc(path)
        lines = [p.text for p in doc.paragraphs if p.text.strip()]
        for tbl in doc.tables:
            for row in tbl.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        lines.append(cell.text)
        return "\n".join(lines)

    # ── Structure ─────────────────────────────────────────────────────────
    def _build(self, raw: str) -> Dict[str, Any]:
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        head  = "\n".join(lines[:15])
        secs  = self._segment(lines)
        skills = list(set(
            self._match_skills(secs.get("skills", []) + secs.get("summary", []))
            + self._match_skills_text(raw)
        ))
        return {
            "raw_text"        : raw,
            "name"            : self._name(lines, head),
            "email"           : ((_EMAIL.findall(head)   or [""])[0]),
            "phone"           : ((_PHONE.findall(head)   or [""])[0]),
            "linkedin"        : ((_LINKEDIN.findall(raw) or [""])[0]),
            "github"          : ((_GITHUB.findall(raw)   or [""])[0]),
            "summary"         : " ".join(secs.get("summary", [])),
            "skills"          : skills,
            "education"       : self._edu(secs.get("education", [])),
            "experience"      : self._exp(secs.get("experience", [])),
            "projects"        : self._proj(secs.get("projects", [])),
            "certifications"  : self._plain(secs.get("certifications", [])),
            "achievements"    : self._plain(secs.get("achievements", [])),
            "word_count"      : len(raw.split()),
            "has_bullets"     : any(l.startswith(_BULLETS) for l in lines),
            "sections_found"  : list(secs.keys()),
        }

    def _name(self, lines: List[str], head: str) -> str:
        # Use spaCy first
        if _NLP:
            doc = _NLP(head[:500])
            for ent in doc.ents:
                if ent.label_ == "PERSON" and len(ent.text.split()) >= 2:
                    return ent.text.strip()
        # Heuristic: first 2-4 word Title Case line
        pat = re.compile(r"^[A-Z][a-zA-Z]+(\s[A-Z][a-zA-Z]+){1,3}$")
        for l in lines[:5]:
            if pat.match(l.strip()) and not _EMAIL.search(l):
                return l.strip()
        return lines[0] if lines else "Unknown"

    def _segment(self, lines: List[str]) -> Dict[str, List[str]]:
        out: Dict[str, List[str]] = {"header": []}
        cur = "header"
        for line in lines:
            k = self._hdr(line)
            if k:
                cur = k
                out.setdefault(cur, [])
            else:
                out[cur].append(line)
        return out

    def _hdr(self, line: str) -> Optional[str]:
        cl = line.strip().lower()
        if not (3 <= len(cl) <= 60) or cl.startswith(_BULLETS):
            return None
        for key, pat in _SEC.items():
            if re.search(pat, cl, re.I):
                return key
        return None

    def _match_skills(self, lines: List[str]) -> List[str]:
        text = " ".join(lines).lower()
        return [s.title() for s in (TECH_SKILLS | SOFT_SKILLS)
                if re.search(r"\b" + re.escape(s) + r"\b", text)]

    def _match_skills_text(self, text: str) -> List[str]:
        t = text.lower()
        return [s.title() for s in TECH_SKILLS
                if re.search(r"\b" + re.escape(s) + r"\b", t)]

    def _edu(self, lines: List[str]) -> List[Dict]:
        entries, cur = [], {}
        for line in lines:
            if _DEGREE.search(line):
                if cur: entries.append(cur)
                cur = {"degree": line.strip(), "institution": "", "year": "", "gpa": ""}
            elif cur:
                if not cur["institution"] and len(line) > 4:
                    cur["institution"] = line.strip()
                m = _GPA.search(line)
                if m: cur["gpa"] = m.group(2)
                y = _YEAR.search(line)
                if y and not cur["year"]: cur["year"] = y.group(0)
        if cur: entries.append(cur)
        if not entries and lines:
            entries = [{"degree":"","institution":" ".join(lines[:2]),"year":"","gpa":""}]
        return entries

    def _exp(self, lines: List[str]) -> List[Dict]:
        entries, cur = [], None
        for line in lines:
            is_b = line.startswith(_BULLETS)
            if _TITLE.search(line) and not is_b and len(line) < 120:
                if cur: entries.append(cur)
                cur = {"title": line.strip(), "company": "", "duration": "",
                       "bullets": [], "quantified_impact": []}
            elif cur:
                if _DATE.search(line):
                    cur["duration"] = line.strip()
                elif is_b:
                    b = re.sub(r"^[•\-●▸∙*–→◦▪]\s*", "", line).strip()
                    cur["bullets"].append(b)
                    cur["quantified_impact"].extend(h[0] for h in _IMPACT.findall(b))
                elif not cur["company"] and len(line) > 3:
                    cur["company"] = line.strip()
        if cur: entries.append(cur)
        return entries

    def _proj(self, lines: List[str]) -> List[Dict]:
        entries, cur = [], None
        for line in lines:
            is_b = line.startswith(_BULLETS)
            if not is_b and 2 < len(line.split()) <= 12:
                if cur: entries.append(cur)
                cur = {"title": line.strip(), "description": [], "tech_stack": [], "links": []}
            elif cur:
                if is_b:
                    cur["description"].append(
                        re.sub(r"^[•\-●▸∙*–→◦▪]\s*", "", line).strip()
                    )
                cur["links"].extend(_URL.findall(line))
                cur["tech_stack"].extend(self._match_skills([line]))
        if cur: entries.append(cur)
        if not entries and lines:
            entries = [{"title":"Projects","description":lines,"tech_stack":[],"links":[]}]
        return entries

    def _plain(self, lines: List[str]) -> List[str]:
        return [re.sub(r"^[•\-●▸∙*–→◦▪]\s*","",l).strip() for l in lines if l.strip()]
