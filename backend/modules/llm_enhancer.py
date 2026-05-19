"""
modules/llm_enhancer.py
AI resume enhancement using Groq (free) or OpenAI.
Primary  : Groq API (free, fast, llama3-70b)
Secondary: OpenAI GPT-4o-mini
Fallback : Rule-based rewriter
"""

import os, re, copy
from typing import Dict, Any, List

# ── Groq Client ───────────────────────────────────────────────────────────────
try:
    from groq import Groq
    _groq_key    = os.getenv("GROQ_API_KEY", "")
    _groq_client = Groq(api_key=_groq_key) if _groq_key else None
    _GROQ        = _groq_client is not None
except Exception:
    _groq_client = None
    _GROQ        = False

# ── OpenAI Client ─────────────────────────────────────────────────────────────
try:
    from openai import OpenAI
    _oai_key    = os.getenv("OPENAI_API_KEY", "")
    _oai_client = OpenAI(api_key=_oai_key) if _oai_key.startswith("sk-") else None
    _OPENAI     = _oai_client is not None
except Exception:
    _oai_client = None
    _OPENAI     = False

print(f"[LLM] Groq: {_GROQ}, OpenAI: {_OPENAI}")

# ── Weak phrase replacements ──────────────────────────────────────────────────
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

FILLERS = r"\b(very|basically|just|really|quite|somewhat|actually)\s+"

SYSTEM_PROMPT = """You are an expert resume writer with 10 years of experience.
Your job is to rewrite resume content to be more impactful and professional.
Rules:
- Start bullets with strong action verbs (Led, Developed, Engineered, Optimized, etc.)
- Keep ALL original facts and numbers
- Do NOT invent fake metrics or percentages
- Be concise and professional
- Return ONLY the rewritten text, nothing else"""


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
            improvements.append("✅ Enhanced professional summary.")

        # Experience
        new_exp = self._exp(parsed.get("experience", []), role)
        enhanced["experience"] = new_exp
        sections["experience"] = new_exp
        total = sum(len(e.get("bullets", [])) for e in parsed.get("experience", []))
        if total:
            improvements.append(f"✅ Rewrote {total} experience bullet(s) with stronger language.")

        # Projects
        new_proj = self._proj(parsed.get("projects", []))
        enhanced["projects"] = new_proj
        sections["projects"] = new_proj
        if parsed.get("projects"):
            improvements.append("✅ Strengthened project descriptions.")

        # Skills
        if parsed.get("skills"):
            sk = sorted(set(parsed["skills"]))
            enhanced["skills"] = sk
            sections["skills"] = sk
            improvements.append("✅ Organized skills alphabetically.")

        if not parsed.get("summary"):
            improvements.append("⚠️  Add a professional summary section.")
        if not parsed.get("github"):
            improvements.append("⚠️  Add your GitHub URL.")
        if not parsed.get("linkedin"):
            improvements.append("⚠️  Add your LinkedIn URL.")

        llm_used = "Groq (Llama3)" if _GROQ else ("OpenAI" if _OPENAI else "Rule-based")
        improvements.append(f"ℹ️  Enhanced using: {llm_used}")

        return {
            "enhanced_parsed"  : enhanced,
            "enhanced_sections": sections,
            "improvements"     : improvements,
        }

    # ── Section rewriters ─────────────────────────────────────────────────────
    def _summary(self, s: str, jd: str, role: str) -> str:
        prompt = (
            f"Target role: {role}\n"
            f"Original summary: {s}\n\n"
            "Rewrite this resume summary to be more professional and impactful. "
            "Keep the same facts. Do NOT add fake numbers. "
            "2-3 sentences maximum. Return ONLY the rewritten text."
        )
        return self._llm(prompt) or self._clean(s)

    def _exp(self, exp: List[Dict], role: str) -> List[Dict]:
        out = []
        for entry in exp:
            e = copy.deepcopy(entry)
            new_bullets = []
            for b in entry.get("bullets", []):
                prompt = (
                    f"Resume bullet point: {b}\n\n"
                    "Rewrite this bullet to be more impactful:\n"
                    "1. Start with a strong action verb\n"
                    "2. Keep ALL original facts and numbers\n"
                    "3. Do NOT add fake metrics\n"
                    "4. Make it concise — one line only\n"
                    "Return ONLY the rewritten bullet, no dash or bullet prefix."
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
                    f"Project: {proj.get('title', '')}\n"
                    f"Bullet: {line}\n\n"
                    "Rewrite to highlight technical impact. "
                    "Start with action verb. Keep original facts. "
                    "No fake metrics. One line only. "
                    "Return ONLY the rewritten line."
                )
                new_l = self._llm(prompt) or self._bullet(line)
                new_desc.append(new_l.strip())
            p["description"] = new_desc if new_desc else proj.get("description", [])
            out.append(p)
        return out

    # ── LLM Call ─────────────────────────────────────────────────────────────
    def _llm(self, prompt: str) -> str:
        """Try Groq first, then OpenAI, then return empty string."""
        # Try Groq
        if _GROQ and _groq_client:
            try:
                r = _groq_client.chat.completions.create(
                    model    = "llama3-70b-8192",
                    messages = [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": prompt},
                    ],
                    max_tokens  = 200,
                    temperature = 0.3,
                )
                result = r.choices[0].message.content.strip()
                if result:
                    return result
            except Exception as e:
                print(f"[Groq] Error: {e}")

        # Try OpenAI
        if _OPENAI and _oai_client:
            try:
                r = _oai_client.chat.completions.create(
                    model    = "gpt-4o-mini",
                    messages = [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": prompt},
                    ],
                    max_tokens  = 200,
                    temperature = 0.3,
                )
                result = r.choices[0].message.content.strip()
                if result:
                    return result
            except Exception as e:
                print(f"[OpenAI] Error: {e}")

        return ""

    # ── Rule-based fallback ───────────────────────────────────────────────────
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
        t = re.sub(FILLERS, " ", t, flags=re.I)
        return re.sub(r"  +", " ", t).strip()
