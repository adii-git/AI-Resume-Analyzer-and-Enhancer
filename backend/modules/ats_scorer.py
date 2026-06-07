"""modules/ats_scorer.py — ATS Scoring Engine"""
import re
from collections import Counter
from typing import Dict, Any, List, Tuple

ROLE_KW: Dict[str, List[str]] = {
    "Software Engineer"  : ["algorithms","data structures","system design","oop","rest api","microservices","git","ci/cd","unit testing","agile","python","java","javascript","docker","kubernetes"],
    "Data Analyst"       : ["sql","python","tableau","power bi","excel","data visualization","statistical analysis","a/b testing","etl","pandas","numpy","kpi","dashboard","reporting"],
    "Data Scientist"     : ["machine learning","deep learning","nlp","tensorflow","pytorch","scikit-learn","statistics","feature engineering","model deployment","mlops","python","sql","neural networks"],
    "DevOps Engineer"    : ["docker","kubernetes","terraform","ansible","jenkins","github actions","aws","azure","gcp","linux","bash","monitoring","ci/cd","infrastructure as code","cloud"],
    "Product Manager"    : ["product roadmap","stakeholder management","user stories","agile","scrum","kpi","market research","competitive analysis","mvp","go-to-market","prioritization","jira"],
    "Frontend Developer" : ["react","vue","angular","javascript","typescript","html","css","responsive design","graphql","webpack","accessibility","figma","ui/ux"],
    "Backend Developer"  : ["rest api","microservices","python","java","node.js","go","sql","nosql","redis","docker","kubernetes","system design","authentication","caching"],
    "General"            : ["communication","teamwork","problem solving","leadership","project management","analytical","collaboration","innovation"],
}
ACTION_VERBS = {"led","managed","developed","designed","built","created","implemented","optimized","improved","increased","reduced","achieved","delivered","launched","deployed","analyzed","architected","automated","streamlined","mentored","scaled","engineered","spearheaded"}
WEAK_PHRASES = ["responsible for","helped with","worked on","assisted in","was part of","duties included","involved in"]
QUANT_RE     = re.compile(r"(\d+%|\$[\d,]+[km]?|\d+[xX]|\d+\s*(million|billion|k\b)|\d+\s*(users|customers|clients|requests))", re.I)


class ATSScorer:
    SUPPORTED_ROLES = list(ROLE_KW.keys())

    def score(self, parsed: Dict[str, Any], jd: str) -> Dict[str, Any]:
        kw_s,kw_d = self._kw(parsed["raw_text"], jd)
        sk_s,sk_d = self._sk(parsed, jd)
        ex_s,ex_d = self._ex(parsed)
        fm_s,fm_d = self._fm(parsed)
        total = round(0.40*kw_s + 0.20*sk_s + 0.20*ex_s + 0.20*fm_s, 1)
        return {
            "total_score": total,
            "breakdown": {
                "keyword_match"     : {"score": round(kw_s,1), "weight": 0.40, "details": kw_d},
                "skills_relevance"  : {"score": round(sk_s,1), "weight": 0.20, "details": sk_d},
                "experience_quality": {"score": round(ex_s,1), "weight": 0.20, "details": ex_d},
                "formatting"        : {"score": round(fm_s,1), "weight": 0.20, "details": fm_d},
            },
        }

    def keyword_gap(self, resume_text: str, jd: str) -> Dict[str, List[str]]:
        kws  = self._jd_kws(jd)
        rlow = resume_text.lower()
        matched = [k for k in kws if re.search(r"\b"+re.escape(k)+r"\b", rlow)]
        missing = [k for k in kws if k not in matched]
        return {"matched": matched[:30], "missing": missing[:30]}

    def section_feedback(self, parsed: Dict[str, Any]) -> Dict[str, List[str]]:
        fb: Dict[str, List[str]] = {}
        tips = []
        if len(parsed.get("skills",[])) < 8: tips.append("Add more technical skills — aim for 10–15.")
        if not tips: tips.append("Skills section looks solid.")
        fb["skills"] = tips
        exp   = parsed.get("experience", [])
        bulls = [b for e in exp for b in e.get("bullets", [])]
        quant = sum(len(e.get("quantified_impact",[])) for e in exp)
        weak  = sum(1 for b in bulls if any(wp in b.lower() for wp in WEAK_PHRASES))
        tips  = []
        if not exp: tips.append("No experience section detected.")
        else:
            if len(bulls) < 3: tips.append("Add more bullet points per role (3–5 each).")
            if quant == 0:     tips.append("Add quantified results: 'reduced load time by 40%'.")
            if weak > 0:       tips.append(f"Replace {weak} weak phrase(s) with action verbs.")
        if not tips: tips.append("Experience section is strong.")
        fb["experience"] = tips
        proj = parsed.get("projects", [])
        tips = []
        if not proj: tips.append("Add a projects section.")
        else:
            if any(not p.get("tech_stack") for p in proj): tips.append("Mention tech stack in each project.")
            if any(not p.get("links") for p in proj):      tips.append("Add GitHub links to projects.")
        if not tips: tips.append("Projects look great.")
        fb["projects"] = tips
        tips = []
        if not parsed.get("has_bullets"):          tips.append("Use bullet points in experience sections.")
        if parsed.get("word_count", 0) < 200:      tips.append("Resume seems too short.")
        if parsed.get("word_count", 0) > 800:      tips.append("Resume may be too long.")
        if not parsed.get("email"):                tips.append("Add your email address.")
        if not parsed.get("linkedin"):             tips.append("Add your LinkedIn URL.")
        if not tips: tips.append("Formatting looks clean.")
        fb["formatting"] = tips
        return fb

    def _kw(self, resume, jd):
        kws  = self._jd_kws(jd)
        if not kws: return 50.0, {"note": "No keywords in JD."}
        rlow = resume.lower()
        wc   = max(len(resume.split()), 1)
        matched, density = [], 0.0
        for k in kws:
            occ = len(re.findall(r"\b"+re.escape(k)+r"\b", rlow))
            if occ: matched.append(k); density += occ/wc
        ratio = len(matched)/len(kws)
        return min(ratio*90 + min(density*500,10), 100), {"jd_keywords": len(kws), "matched": len(matched), "ratio": round(ratio,3)}

    def _sk(self, parsed, jd):
        from modules.parser import TECH_SKILLS, SOFT_SKILLS
        skills = [s.lower() for s in parsed.get("skills", [])]
        jd_low = jd.lower()
        best_role, best_cnt, best_ov = "General", 0, 0.0
        for role, kws in ROLE_KW.items():
            cnt = sum(1 for k in kws if re.search(r"\b"+re.escape(k)+r"\b", jd_low))
            if cnt > best_cnt:
                best_cnt = cnt; best_role = role
                m = sum(1 for k in kws if any(re.search(r"\b"+re.escape(k)+r"\b", s) for s in skills))
                best_ov = m / max(len(kws), 1)
        return min(min(len(skills)/15*50, 50) + best_ov*50, 100), {"skills_found": len(skills), "best_role": best_role}

    def _ex(self, parsed):
        exp = parsed.get("experience", [])
        if not exp: return 0.0, {"note": "No experience."}
        score = 20
        bulls = [b for e in exp for b in e.get("bullets", [])]
        quant = sum(len(e.get("quantified_impact",[])) for e in exp)
        vratio = sum(1 for b in bulls if b and b.lower().split()[0] in ACTION_VERBS) / max(len(bulls),1)
        score += vratio*20 + min(quant/3*30,30) + (20 if len(exp)>=2 else 10)
        weak = sum(1 for b in bulls if any(wp in b.lower() for wp in WEAK_PHRASES))
        if weak==0: score+=10
        return min(score,100), {"roles": len(exp), "quantified": quant, "verb_ratio": round(vratio,2)}

    def _fm(self, parsed):
        s = 0
        if parsed.get("has_bullets"): s+=20
        if parsed.get("email"):       s+=15
        if parsed.get("phone"):       s+=10
        if parsed.get("linkedin"):    s+=10
        if parsed.get("github"):      s+=5
        wc = parsed.get("word_count",0)
        s += 20 if 200<=wc<=700 else (10 if wc>0 else 0)
        if parsed.get("summary"):     s+=10
        if len(parsed.get("sections_found",[]))>=3: s+=10
        return min(s,100), {"word_count": wc}

    def _jd_kws(self, jd):
        from modules.parser import TECH_SKILLS, SOFT_SKILLS
        jd_low = jd.lower()
        vocab  = [k for k in (TECH_SKILLS|SOFT_SKILLS) if re.search(r"\b"+re.escape(k)+r"\b", jd_low)]
        words  = re.findall(r"\b[a-zA-Z][a-zA-Z+#.\-]{3,}\b", jd)
        freq   = [w.lower() for w,c in Counter(w.lower() for w in words).items() if c>=2]
        return list(set(vocab+freq))
