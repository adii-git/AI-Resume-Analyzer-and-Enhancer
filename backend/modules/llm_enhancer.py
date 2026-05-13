"""
modules/llm_enhancer.py
Enhances resume bullets using OpenAI GPT-4o-mini.
Falls back to rule-based rewriting with NO api key required.
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
    "responsible for":"Led","helped with":"Contributed to","worked on":"Developed",
    "assisted in":"Supported","was part of":"Collaborated on",
    "duties included":"Delivered","tasked with":"Executed","involved in":"Drove",
    "used":"Leveraged","helped":"Facilitated",
}
STYLE = [(r"\bvery\s+",""), (r"\bbasically\s+",""), (r"\bjust\s+",""),
         (r"\bI\s+",""), (r"\bmy\s+",""), (r"  +"," ")]
QUANT = re.compile(r"(\d+%|\$[\d,]+[km]?|\d+[xX]|\d+\s*(million|billion|k\b)|\d+\s*(users|customers|clients))", re.I)


class LLMEnhancer:
    def enhance(self, parsed: Dict[str, Any], jd: str, role: str = "General") -> Dict[str, Any]:
        enhanced     = copy.deepcopy(parsed)
        sections     : Dict[str, Any] = {}
        improvements : List[str]      = []

        if parsed.get("summary"):
            new = self._summary(parsed["summary"], jd, role)
            enhanced["summary"] = new; sections["summary"] = new
            if new != parsed["summary"]: improvements.append("✅ Rewrote professional summary to be more impactful.")

        new_exp = self._exp(parsed.get("experience",[]), role)
        enhanced["experience"] = new_exp; sections["experience"] = new_exp
        total = sum(len(e.get("bullets",[])) for e in parsed.get("experience",[]))
        if total: improvements.append(f"✅ Enhanced {total} experience bullet(s) with action verbs and metrics.")

        new_proj = self._proj(parsed.get("projects",[]))
        enhanced["projects"] = new_proj; sections["projects"] = new_proj
        if parsed.get("projects"): improvements.append("✅ Rewrote project descriptions to highlight technical impact.")

        if parsed.get("skills"):
            sk = sorted(parsed["skills"])
            enhanced["skills"] = sk; sections["skills"] = sk
            improvements.append("✅ Organized skills alphabetically.")

        if not parsed.get("summary"):   improvements.append("⚠️  Add a 3–4 line professional summary.")
        if not parsed.get("github"):    improvements.append("⚠️  Add your GitHub profile URL.")
        if not parsed.get("linkedin"):  improvements.append("⚠️  Add your LinkedIn URL.")

        return {"enhanced_parsed": enhanced, "enhanced_sections": sections, "improvements": improvements}

    def _summary(self, s: str, jd: str, role: str) -> str:
        p = (f"Target role: {role}\nJD excerpt: {jd[:400]}\nOriginal summary: {s}\n\n"
             "Rewrite in 3–4 lines. Concise, impactful, third person. Return ONLY rewritten text.")
        return self._llm(p) or self._rule_sum(s)

    def _exp(self, exp: List[Dict], role: str) -> List[Dict]:
        out = []
        for entry in exp:
            e = copy.deepcopy(entry)
            new_b = []
            for b in entry.get("bullets",[]):
                p = (f"Role: {role}\nBullet: {b}\n\n"
                     "Rewrite using XYZ impact formula. Start with action verb. "
                     "Add plausible metric if none. Return ONE line, no dash prefix.")
                new_b.append((self._llm(p) or self._rule_b(b)).strip())
            e["bullets"] = new_b or entry.get("bullets",[])
            e["quantified_impact"] = [h[0] for b in e["bullets"] for h in QUANT.findall(b)]
            out.append(e)
        return out

    def _proj(self, projects: List[Dict]) -> List[Dict]:
        out = []
        for proj in projects:
            p2 = copy.deepcopy(proj)
            desc = []
            for line in proj.get("description",[]):
                prompt = (f"Project: {proj.get('title','')}\nLine: {line}\n\n"
                          "Rewrite to highlight impact and tech. Start with action verb. ONE line.")
                desc.append((self._llm(prompt) or self._rule_b(line)).strip())
            p2["description"] = desc or proj.get("description",[])
            out.append(p2)
        return out

    def _llm(self, prompt: str) -> str:
        if not _OPENAI or not _client: return ""
        try:
            r = _client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role":"system","content":"You are an expert resume writer. Follow instructions exactly. Be concise."},
                    {"role":"user","content":prompt}],
                max_tokens=250, temperature=0.3)
            return r.choices[0].message.content.strip()
        except Exception as e:
            print(f"[LLM] {e}"); return ""

    def _rule_b(self, text: str) -> str:
        t = text.strip()
        for weak, strong in UPGRADES.items():
            t = re.sub(r"(?i)^"+re.escape(weak)+r"\s*", strong+" ", t)
        for pat, rep in STYLE:
            t = re.sub(pat, rep, t, flags=re.I).strip()
        if t: t = t[0].upper() + t[1:]
        if not QUANT.search(t) and len(t) > 20:
            t = t.rstrip(".") + ", improving team efficiency by ~20%."
        return t

    def _rule_sum(self, text: str) -> str:
        t = re.sub(r"\bI am\b","A", text, flags=re.I)
        t = re.sub(r"\bI\b","", t, flags=re.I)
        return re.sub(r"  +"," ", t).strip()
