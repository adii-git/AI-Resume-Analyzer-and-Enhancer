"""
modules/llm_enhancer.py
Sends FULL resume to Groq/OpenAI for comprehensive enhancement.
Fixes merged words AND improves content simultaneously.
"""

import os, re, copy, json
from typing import Dict, Any, List, Optional

# Groq
try:
    from groq import Groq

    _gkey = os.getenv("GROQ_API_KEY", "")
    print("Groq key exists:", bool(_gkey))

    _gclient = Groq(api_key=_gkey) if _gkey else None
    _GROQ = _gclient is not None

except Exception as e:
    print("GROQ ERROR:", e)

    _gclient = None
    _GROQ = False

# OpenAI
try:
    from openai import OpenAI
    _okey   = os.getenv("OPENAI_API_KEY", "")
    _oclient= OpenAI(api_key=_okey) if _okey.startswith("sk-") else None
    _OPENAI = _oclient is not None
except Exception:
    _oclient= None
    _OPENAI = False

print(f"[LLM] Groq={_GROQ}, OpenAI={_OPENAI}")

UPGRADES = {
    "responsible for": "Led", "helped with": "Contributed to",
    "worked on": "Developed", "assisted in": "Supported",
    "was part of": "Collaborated on", "duties included": "Delivered",
    "tasked with": "Executed", "involved in": "Drove",
}
FILLERS = r"\b(very|basically|just|really|quite|somewhat|actually)\s+"

SYSTEM = """You are an expert resume writer with 10+ years experience at top tech companies.
Your task: Fix merged words AND enhance resume content.
Rules:
- Fix all merged/concatenated words (e.g. "BuiltaSystem" → "Built a System")  
- Start every bullet with a strong action verb (Led, Developed, Engineered, Optimized, etc.)
- Keep ALL original facts - do NOT invent fake metrics
- Improve clarity, impact, and professionalism
- Return ONLY valid JSON, no extra text"""


class LLMEnhancer:

    def enhance(self, parsed: Dict[str, Any], jd: str,
                role: str = "General") -> Dict[str, Any]:
        enhanced    = copy.deepcopy(parsed)
        sections    : Dict[str, Any] = {}
        improvements: List[str]      = []

        if _GROQ or _OPENAI:
            result = self._full_enhance(parsed, jd, role)
            if result:
                enhanced    = result
                sections    = {
                    "summary"   : enhanced.get("summary", ""),
                    "experience": enhanced.get("experience", []),
                    "projects"  : enhanced.get("projects", []),
                    "skills"    : enhanced.get("skills", []),
                }
                model = "llama-3.3-70b-versatile" if _GROQ else "GPT-4o-mini"
                improvements.append(f"✅ Full resume enhanced using {model}.")
                improvements.append("✅ Fixed merged words and improved all bullet points.")
                improvements.append("✅ Applied strong action verbs throughout.")
            else:
                self._rule_enhance(parsed, enhanced, sections, improvements)
                improvements.append("⚠️  AI enhancement failed. Rule-based applied.")
        else:
            self._rule_enhance(parsed, enhanced, sections, improvements)
            improvements.append("⚠️  No AI key configured. Rule-based enhancement applied.")

        if not parsed.get("summary"):
            improvements.append("⚠️  Add a professional summary section.")
        if not parsed.get("github"):
            improvements.append("⚠️  Add your GitHub URL.")
        if not parsed.get("linkedin"):
            improvements.append("⚠️  Add your LinkedIn URL.")

        return {"enhanced_parsed": enhanced, "enhanced_sections": sections, "improvements": improvements}

    # ── Full resume enhancement ───────────────────────────────────────────────
    def _full_enhance(self, parsed: Dict, jd: str, role: str) -> Optional[Dict]:
        resume_text = self._to_text(parsed)
        prompt = f"""Target Role: {role}
Job Description (first 300 chars): {jd[:300]}

RESUME TO ENHANCE:
{resume_text}

Instructions:
1. Fix ALL merged words (e.g. "BuiltaSystem" → "Built a System", "ImplementedATSscoring" → "Implemented ATS scoring")
2. Rewrite bullets to start with strong action verbs
3. Keep ALL original facts
4. Do NOT add fake numbers or metrics
5. Improve grammar and clarity

Return this EXACT JSON (no markdown, no extra text):
{{
  "summary": "enhanced summary text here",
  "experience": [
    {{
      "title": "job title",
      "company": "company",
      "duration": "dates",
      "bullets": ["bullet 1", "bullet 2"]
    }}
  ],
  "projects": [
    {{
      "title": "project name",
      "description": ["bullet 1", "bullet 2"]
    }}
  ]
}}"""

        raw = self._call(prompt, max_tokens=3000)
        if not raw:
            return None

        try:
            # Clean JSON
            raw = raw.strip()
            raw = re.sub(r"```json\s*", "", raw)
            raw = re.sub(r"```\s*", "", raw)
            raw = raw.strip()

            # Find JSON object
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            if start == -1 or end == 0:
                return None
            raw = raw[start:end]

            data = json.loads(raw)

            # Merge into parsed copy
            enhanced = copy.deepcopy(parsed)

            if data.get("summary"):
                enhanced["summary"] = data["summary"]

            if data.get("experience") and parsed.get("experience"):
                for i, item in enumerate(data["experience"]):
                    if i < len(enhanced["experience"]):
                        if item.get("bullets"):
                            enhanced["experience"][i]["bullets"] = item["bullets"]
                        # Update title if AI fixed merged words
                        if item.get("title") and len(item["title"]) > 3:
                            enhanced["experience"][i]["title"] = item["title"]
                        if item.get("company") and len(item["company"]) > 1:
                            enhanced["experience"][i]["company"] = item["company"]

            if data.get("projects") and parsed.get("projects"):
                for i, item in enumerate(data["projects"]):
                    if i < len(enhanced["projects"]):
                        if item.get("description"):
                            enhanced["projects"][i]["description"] = item["description"]
                        if item.get("title") and len(item["title"]) > 2:
                            enhanced["projects"][i]["title"] = item["title"]

            if parsed.get("skills"):
                enhanced["skills"] = sorted(set(parsed["skills"]))

            return enhanced

        except Exception as e:
            print(f"[LLM] Parse error: {e} | Raw: {raw[:300]}")
            return None

    def _to_text(self, parsed: Dict) -> str:
        lines = []
        if parsed.get("name"):    lines.append(f"Name: {parsed['name']}")
        if parsed.get("summary"): lines.append(f"\nSUMMARY:\n{parsed['summary']}")
        if parsed.get("experience"):
            lines.append("\nEXPERIENCE:")
            for exp in parsed["experience"]:
                lines.append(f"  Role: {exp.get('title','')} at {exp.get('company','')}")
                for b in exp.get("bullets", []):
                    lines.append(f"    - {b}")
        if parsed.get("projects"):
            lines.append("\nPROJECTS:")
            for proj in parsed["projects"]:
                lines.append(f"  Project: {proj.get('title','')}")
                for d in proj.get("description", []):
                    lines.append(f"    - {d}")
        return "\n".join(lines)

    # ── LLM call ─────────────────────────────────────────────────────────────
    def _call(self, prompt: str, max_tokens: int = 3000) -> str:
        # Try Groq first (free and fast)
        if _GROQ and _gclient:
            try:
                r = _gclient.chat.completions.create(
                    model    = "llama-3.3-70b-versatile",
                    messages = [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user",   "content": prompt},
                    ],
                    max_tokens  = max_tokens,
                    temperature = 0.2,
                )
                result = r.choices[0].message.content.strip()
                if result: return result
            except Exception as e:
                print(f"[Groq] Error: {e}")

        # Try OpenAI
        if _OPENAI and _oclient:
            try:
                r = _oclient.chat.completions.create(
                    model    = "gpt-4o-mini",
                    messages = [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user",   "content": prompt},
                    ],
                    max_tokens  = max_tokens,
                    temperature = 0.2,
                )
                result = r.choices[0].message.content.strip()
                if result: return result
            except Exception as e:
                print(f"[OpenAI] Error: {e}")

        return ""

    # ── Rule-based fallback ───────────────────────────────────────────────────
    def _rule_enhance(self, parsed, enhanced, sections, improvements):
        if parsed.get("summary"):
            s = self._clean(parsed["summary"])
            enhanced["summary"] = s; sections["summary"] = s

        new_exp = []
        for entry in parsed.get("experience", []):
            e = copy.deepcopy(entry)
            e["bullets"] = [self._bullet(b) for b in entry.get("bullets", [])]
            new_exp.append(e)
        enhanced["experience"] = new_exp; sections["experience"] = new_exp

        new_proj = []
        for proj in parsed.get("projects", []):
            p = copy.deepcopy(proj)
            p["description"] = [self._bullet(d) for d in proj.get("description", [])]
            new_proj.append(p)
        enhanced["projects"] = new_proj; sections["projects"] = new_proj

        if parsed.get("skills"):
            sk = sorted(set(parsed["skills"]))
            enhanced["skills"] = sk; sections["skills"] = sk
        improvements.append("✅ Applied rule-based improvements.")

    def _bullet(self, text: str) -> str:
        t = text.strip()
        if not t: return t
        tl = t.lower()
        for weak, strong in UPGRADES.items():
            if tl.startswith(weak + " ") or tl == weak:
                t = strong + " " + t[len(weak):].lstrip(); break
        t = re.sub(FILLERS, " ", t, flags=re.I).strip()
        t = re.sub(r"  +", " ", t).strip()
        if t: t = t[0].upper() + t[1:]
        if t and t[-1] not in ".!?": t += "."
        return t

    def _clean(self, text: str) -> str:
        t = re.sub(r"\bI am\b", "A", text, flags=re.I)
        t = re.sub(r"\bI\b", "", t, flags=re.I)
        return re.sub(r"  +", " ", t).strip()
