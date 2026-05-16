"""
modules/llm_enhancer.py
AI resume enhancement - visible improvements without fake metrics.
"""

import os, re, copy
from typing import Dict, Any, List

try:
    from openai import OpenAI as _OAI
    _key    = os.getenv("OPENAI_API_KEY", "")
    _client = _OAI(api_key=_key) if _key.startswith("sk-") else None
    _OPENAI = _client is not None
except Exception:
    _client = None
    _OPENAI = False

UPGRADES = {
    "responsible for": "Led",
    "helped with"    : "Contributed to",
    "worked on"      : "Developed",
    "assisted in"    : "Supported",
    "was part of"    : "Collaborated on",
    "duties included": "Delivered",
    "tasked with"    : "Executed",
    "involved in"    : "Drove",
    "used"           : "Utilized",
    "made"           : "Developed",
    "did"            : "Executed",
}

# Words to remove (filler)
FILLERS = r"\b(very|basically|just|really|quite|somewhat|actually)\s+"


class LLMEnhancer:

    def enhance(self, parsed: Dict[str, Any], jd: str,
                role: str = "General") -> Dict[str, Any]:
        enhanced     = copy.deepcopy(parsed)
        sections     : Dict[str, Any] = {}
        improvements : List[str]      = []

        # Summary
        if parsed.get("summary"):
            new = self._summary(parsed["summary"], jd, role)
            enhanced["summary"] = new
            sections["summary"] = new
            if new != parsed["summary"]:
                improvements.append("✅ Enhanced professional summary.")

        # Experience
        new_exp = self._exp(parsed.get("experience", []), role)
        enhanced["experience"] = new_exp
        sections["experience"] = new_exp
        total = sum(len(e.get("bullets", [])) for e in parsed.get("experience", []))
        if total:
            improvements.append(f"✅ Strengthened {total} experience bullet(s).")

        # Projects
        new_proj = self._proj(parsed.get("projects", []))
        enhanced["projects"] = new_proj
        sections["projects"] = new_proj
        if parsed.get("projects"):
            improvements.append("✅ Improved project descriptions.")

        # Skills
        if parsed.get("skills"):
            sk = sorted(set(parsed["skills"]))
            enhanced["skills"] = sk
            sections["skills"] = sk
            improvements.append("✅ Organized skills alphabetically.")

        if not parsed.get("summary"):
            improvements.append("⚠️  Add a professional summary section.")
        if not parsed.get("github"):
            improvements.append("⚠️  Add your GitHub URL to the header.")
        if not parsed.get("linkedin"):
            improvements.append("⚠️  Add your LinkedIn URL to the header.")

        return {
            "enhanced_parsed"  : enhanced,
            "enhanced_sections": sections,
            "improvements"     : improvements,
        }

    def _summary(self, s: str, jd: str, role: str) -> str:
        prompt = (
            f"Target role: {role}\nOriginal summary:\n{s}\n\n"
            "Rewrite to be more professional and impactful. "
            "Keep same facts. No fake numbers. 2-3 sentences. "
            "Return ONLY the rewritten summary."
        )
        return self._llm(prompt) or self._clean(s)

    def _exp(self, exp: List[Dict], role: str) -> List[Dict]:
        out = []
        for entry in exp:
            e = copy.deepcopy(entry)
            new_bullets = []
            for b in entry.get("bullets", []):
                prompt = (
                    f"Resume bullet: {b}\n\n"
                    "Rewrite to be more impactful:\n"
                    "- Start with strong action verb\n"
                    "- Keep ALL original facts and any existing numbers\n"
                    "- Do NOT invent metrics\n"
                    "- One line only, no prefix\n"
                    "Return ONLY the rewritten bullet."
                )
                new_b = self._llm(prompt) or self._bullet(b)
                new_bullets.append(new_b.strip())
            e["bullets"] = new_bullets if new_bullets else entry.get("bullets", [])
            out.append(e)
        return out

    def _proj(self, projects: List[Dict]) -> List[Dict]:
        out = []
        for proj in projects:
            p = copy.deepcopy(proj)
            new_desc = []
            for line in proj.get("description", []):
                prompt = (
                    f"Project bullet: {line}\n\n"
                    "Rewrite to highlight technical impact. "
                    "Start with action verb. Keep original facts. "
                    "No fake metrics. One line. Return ONLY the rewritten line."
                )
                new_l = self._llm(prompt) or self._bullet(line)
                new_desc.append(new_l.strip())
            p["description"] = new_desc if new_desc else proj.get("description", [])
            out.append(p)
        return out

    def _llm(self, prompt: str) -> str:
        if not _OPENAI or not _client: return ""
        try:
            r = _client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content":
                     "You are an expert resume writer. "
                     "Never add fake metrics. Keep all original facts. "
                     "Only improve language for clarity and impact."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200, temperature=0.3,
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            print(f"[LLM] {e}"); return ""

    def _bullet(self, text: str) -> str:
        """Rule-based: replace weak openers, clean fillers, capitalize."""
        t = text.strip()
        if not t: return t

        # Replace weak openers
        t_lower = t.lower()
        for weak, strong in UPGRADES.items():
            if t_lower.startswith(weak + " ") or t_lower == weak:
                t = strong + " " + t[len(weak):].lstrip()
                break

        # Remove filler words
        t = re.sub(FILLERS, " ", t, flags=re.I).strip()
        t = re.sub(r"  +", " ", t).strip()

        # Capitalize first letter
        if t:
            t = t[0].upper() + t[1:]

        # End with period
        if t and t[-1] not in ".!?":
            t += "."

        return t

    def _clean(self, text: str) -> str:
        """Basic summary cleanup."""
        t = re.sub(r"\bI am\b", "A", text, flags=re.I)
        t = re.sub(r"\bI\b", "", t, flags=re.I)
        t = re.sub(FILLERS, " ", t, flags=re.I)
        return re.sub(r"  +", " ", t).strip()
