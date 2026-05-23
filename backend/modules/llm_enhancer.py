"""
modules/llm_enhancer.py
AI resume enhancement - sends full resume context to Groq/OpenAI
for comprehensive rewriting, not just bullet-by-bullet.
"""

import os, re, copy
from typing import Dict, Any, List

# ── Groq ─────────────────────────────────────────────────────────────────────
try:
    from groq import Groq
    _groq_key    = os.getenv("GROQ_API_KEY", "")
    _groq_client = Groq(api_key=_groq_key) if _groq_key else None
    _GROQ        = _groq_client is not None
except Exception:
    _groq_client = None
    _GROQ        = False

# ── OpenAI ────────────────────────────────────────────────────────────────────
try:
    from openai import OpenAI
    _oai_key    = os.getenv("OPENAI_API_KEY", "")
    _oai_client = OpenAI(api_key=_oai_key) if _oai_key.startswith("sk-") else None
    _OPENAI     = _oai_client is not None
except Exception:
    _oai_client = None
    _OPENAI     = False

print(f"[LLM] Groq: {_GROQ}, OpenAI: {_OPENAI}")

UPGRADES = {
    "responsible for": "Led",
    "helped with"    : "Contributed to",
    "worked on"      : "Developed",
    "assisted in"    : "Supported",
    "was part of"    : "Collaborated on",
    "duties included": "Delivered",
    "tasked with"    : "Executed",
    "involved in"    : "Drove",
}
FILLERS = r"\b(very|basically|just|really|quite|somewhat|actually)\s+"


class LLMEnhancer:

    def enhance(self, parsed: Dict[str, Any], jd: str,
                role: str = "General") -> Dict[str, Any]:
        enhanced     = copy.deepcopy(parsed)
        sections     : Dict[str, Any] = {}
        improvements : List[str]      = []

        llm_available = _GROQ or _OPENAI

        if llm_available:
            # ── Send ENTIRE resume to AI at once for best results ──────────
            enhanced_data = self._enhance_full_resume(parsed, jd, role)
            if enhanced_data:
                enhanced     = enhanced_data
                sections     = {
                    "summary"   : enhanced.get("summary", ""),
                    "experience": enhanced.get("experience", []),
                    "projects"  : enhanced.get("projects", []),
                    "skills"    : enhanced.get("skills", []),
                }
                improvements.append("✅ Full resume enhanced using AI.")
                improvements.append(f"ℹ️  Model: {'Groq Llama3-70b' if _GROQ else 'GPT-4o-mini'}")
            else:
                # Fallback to section-by-section
                self._rule_enhance(parsed, enhanced, sections, improvements)
        else:
            self._rule_enhance(parsed, enhanced, sections, improvements)
            improvements.append("⚠️  No AI key found. Using rule-based enhancement.")

        if not parsed.get("summary"):
            improvements.append("⚠️  Add a professional summary section.")
        if not parsed.get("github"):
            improvements.append("⚠️  Add your GitHub URL.")
        if not parsed.get("linkedin"):
            improvements.append("⚠️  Add your LinkedIn URL.")

        return {
            "enhanced_parsed"  : enhanced,
            "enhanced_sections": sections,
            "improvements"     : improvements,
        }

    def _enhance_full_resume(self, parsed: Dict, jd: str, role: str) -> Optional[Dict]:
        """
        Send the ENTIRE resume as one prompt to AI.
        AI fixes spacing issues AND enhances content simultaneously.
        Returns enhanced parsed dict or None if failed.
        """
        # Build resume text
        resume_text = self._build_resume_text(parsed)

        prompt = f"""You are an expert resume writer. I have a resume with some formatting issues (merged words without spaces). Please:

1. Fix any merged/concatenated words (e.g., "BuiltaSystem" should be "Built a System")
2. Rewrite ALL bullet points to be more impactful using strong action verbs
3. Keep ALL original facts - do NOT add fake metrics
4. Make the professional summary more compelling
5. Improve grammar and clarity throughout

Target Role: {role}
Job Description: {jd[:300]}

RESUME TO ENHANCE:
{resume_text}

Please return the enhanced resume in this EXACT JSON format:
{{
  "summary": "enhanced summary here",
  "experience": [
    {{
      "title": "job title",
      "company": "company name",
      "duration": "dates",
      "bullets": ["bullet 1", "bullet 2", "bullet 3"]
    }}
  ],
  "projects": [
    {{
      "title": "project name",
      "description": ["bullet 1", "bullet 2"]
    }}
  ]
}}

Return ONLY the JSON, no other text."""

        result = self._llm(prompt, max_tokens=2000)
        if not result:
            return None

        try:
            import json
            # Clean up response
            result = result.strip()
            if result.startswith("```"):
                result = re.sub(r"```json?\n?", "", result)
                result = result.replace("```", "")
            result = result.strip()

            data = json.loads(result)

            # Merge back into parsed
            enhanced = copy.deepcopy(parsed)

            if data.get("summary"):
                enhanced["summary"] = data["summary"]

            if data.get("experience"):
                for i, exp_item in enumerate(data["experience"]):
                    if i < len(enhanced["experience"]):
                        if exp_item.get("bullets"):
                            enhanced["experience"][i]["bullets"] = exp_item["bullets"]
                        if exp_item.get("title"):
                            enhanced["experience"][i]["title"] = exp_item["title"]

            if data.get("projects"):
                for i, proj_item in enumerate(data["projects"]):
                    if i < len(enhanced["projects"]):
                        if proj_item.get("description"):
                            enhanced["projects"][i]["description"] = proj_item["description"]

            if parsed.get("skills"):
                enhanced["skills"] = sorted(set(parsed["skills"]))

            return enhanced

        except Exception as e:
            print(f"[LLM] JSON parse error: {e}, result: {result[:200]}")
            return None

    def _build_resume_text(self, parsed: Dict) -> str:
        """Build a readable resume text from parsed data."""
        lines = []

        if parsed.get("name"):
            lines.append(f"Name: {parsed['name']}")

        if parsed.get("summary"):
            lines.append(f"\nSUMMARY:\n{parsed['summary']}")

        if parsed.get("experience"):
            lines.append("\nEXPERIENCE:")
            for exp in parsed["experience"]:
                lines.append(f"  {exp.get('title','')} at {exp.get('company','')}")
                for b in exp.get("bullets", []):
                    lines.append(f"    - {b}")

        if parsed.get("projects"):
            lines.append("\nPROJECTS:")
            for proj in parsed["projects"]:
                lines.append(f"  {proj.get('title','')}")
                for d in proj.get("description", []):
                    lines.append(f"    - {d}")

        return "\n".join(lines)

    def _rule_enhance(self, parsed, enhanced, sections, improvements):
        """Rule-based fallback enhancement."""
        if parsed.get("summary"):
            new = self._clean(parsed["summary"])
            enhanced["summary"] = new
            sections["summary"] = new

        new_exp = []
        for entry in parsed.get("experience", []):
            e = copy.deepcopy(entry)
            e["bullets"] = [self._bullet(b) for b in entry.get("bullets", [])]
            new_exp.append(e)
        enhanced["experience"] = new_exp
        sections["experience"] = new_exp

        new_proj = []
        for proj in parsed.get("projects", []):
            p = copy.deepcopy(proj)
            p["description"] = [self._bullet(d) for d in proj.get("description", [])]
            new_proj.append(p)
        enhanced["projects"] = new_proj
        sections["projects"] = new_proj

        if parsed.get("skills"):
            sk = sorted(set(parsed["skills"]))
            enhanced["skills"] = sk
            sections["skills"] = sk

        improvements.append("✅ Applied rule-based improvements.")

    def _llm(self, prompt: str, max_tokens: int = 300) -> str:
        if _GROQ and _groq_client:
            try:
                r = _groq_client.chat.completions.create(
                    model    = "llama3-70b-8192",
                    messages = [
                        {"role": "system", "content": "You are an expert resume writer. Follow instructions exactly."},
                        {"role": "user",   "content": prompt},
                    ],
                    max_tokens  = max_tokens,
                    temperature = 0.3,
                )
                return r.choices[0].message.content.strip()
            except Exception as e:
                print(f"[Groq] {e}")

        if _OPENAI and _oai_client:
            try:
                r = _oai_client.chat.completions.create(
                    model    = "gpt-4o-mini",
                    messages = [
                        {"role": "system", "content": "You are an expert resume writer. Follow instructions exactly."},
                        {"role": "user",   "content": prompt},
                    ],
                    max_tokens  = max_tokens,
                    temperature = 0.3,
                )
                return r.choices[0].message.content.strip()
            except Exception as e:
                print(f"[OpenAI] {e}")

        return ""

    def _bullet(self, text: str) -> str:
        t = text.strip()
        if not t: return t
        t_lower = t.lower()
        for weak, strong in UPGRADES.items():
            if t_lower.startswith(weak + " ") or t_lower == weak:
                t = strong + " " + t[len(weak):].lstrip()
                break
        t = re.sub(FILLERS, " ", t, flags=re.I).strip()
        t = re.sub(r"  +", " ", t).strip()
        if t: t = t[0].upper() + t[1:]
        if t and t[-1] not in ".!?": t += "."
        return t

    def _clean(self, text: str) -> str:
        t = re.sub(r"\bI am\b", "A", text, flags=re.I)
        t = re.sub(r"\bI\b", "", t, flags=re.I)
        return re.sub(r"  +", " ", t).strip()


from typing import Optional
