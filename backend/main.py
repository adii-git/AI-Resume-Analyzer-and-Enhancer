"""
main.py — FastAPI entry point
Run: uvicorn main:app --reload --port 8000
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn, uuid, shutil

from modules.parser       import ResumeParser
from modules.ats_scorer   import ATSScorer
from modules.embeddings   import EmbeddingEngine
from modules.llm_enhancer import LLMEnhancer
from modules.pdf_gen      import PDFGenerator

app = FastAPI(title="ATS Resume Analyzer", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

parser    = ResumeParser()
scorer    = ATSScorer()
embedder  = EmbeddingEngine()
enhancer  = LLMEnhancer()
pdf_gen   = PDFGenerator()

# ── Schemas ──────────────────────────────────────────────────────────────────
class AnalyzeReq(BaseModel):
    file_id: str
    job_description: str
    target_role: Optional[str] = "General"

class EnhanceReq(BaseModel):
    file_id: str
    job_description: str
    target_role: Optional[str] = "General"

class CompareReq(BaseModel):
    file_ids: List[str]
    job_description: str

# ── Routes ───────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    name = file.filename or ""
    if not (name.endswith(".pdf") or name.endswith(".docx")):
        raise HTTPException(400, "Only PDF and DOCX accepted.")
    ext     = ".pdf" if name.endswith(".pdf") else ".docx"
    fid     = str(uuid.uuid4())
    fpath   = os.path.join(UPLOAD_DIR, fid + ext)
    with open(fpath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        parsed = parser.parse(fpath)
    except Exception as e:
        os.remove(fpath)
        raise HTTPException(422, str(e))
    return {"file_id": fid, "filename": name, "parsed": parsed}

@app.post("/analyze")
def analyze(req: AnalyzeReq):
    fp     = _find(req.file_id)
    parsed = parser.parse(fp)
    ats    = scorer.score(parsed, req.job_description)
    sim    = embedder.compute_similarity(parsed["raw_text"], req.job_description)
    gaps   = scorer.keyword_gap(parsed["raw_text"], req.job_description)
    fb     = scorer.section_feedback(parsed)
    return {
        "ats_score"       : ats["total_score"],
        "score_breakdown" : ats["breakdown"],
        "similarity_score": round(sim * 100, 2),
        "matched_keywords": gaps["matched"],
        "missing_keywords": gaps["missing"],
        "feedback"        : fb,
        "parsed"          : parsed,
    }

@app.post("/enhance")
def enhance(req: EnhanceReq):
    fp      = _find(req.file_id)
    parsed  = parser.parse(fp)
    result  = enhancer.enhance(parsed, req.job_description, req.target_role)
    before  = scorer.score(parsed,                       req.job_description)["total_score"]
    after   = scorer.score(result["enhanced_parsed"],    req.job_description)["total_score"]
    out_pdf = os.path.join(UPLOAD_DIR, req.file_id + "_enhanced.pdf")
    pdf_gen.generate(result["enhanced_parsed"], out_pdf)
    return {
        "original_score"    : before,
        "enhanced_score"    : after,
        "improvements"      : result["improvements"],
        "enhanced_sections" : result["enhanced_sections"],
        "original_parsed"   : parsed,
        "download_url"      : f"/download/{req.file_id}_enhanced",
    }

@app.post("/compare")
def compare(req: CompareReq):
    ranked = []
    for fid in req.file_ids:
        try:
            parsed = parser.parse(_find(fid))
            sc     = scorer.score(parsed, req.job_description)
            sim    = embedder.compute_similarity(parsed["raw_text"], req.job_description)
            ranked.append({
                "file_id"   : fid,
                "name"      : parsed.get("name", "Unknown"),
                "ats_score" : sc["total_score"],
                "similarity": round(sim * 100, 2),
                "top_skills": parsed.get("skills", [])[:8],
                "breakdown" : sc["breakdown"],
            })
        except Exception as e:
            ranked.append({"file_id": fid, "name": "Error", "ats_score": 0,
                           "similarity": 0, "top_skills": [], "breakdown": {}, "error": str(e)})
    ranked.sort(key=lambda x: x["ats_score"], reverse=True)
    return {"ranked": ranked, "total": len(ranked)}

@app.get("/download/{file_id}")
def download(file_id: str):
    safe = "".join(c for c in file_id if c.isalnum() or c in "-_")
    path = os.path.join(UPLOAD_DIR, safe + ".pdf")
    if not os.path.exists(path):
        raise HTTPException(404, "File not found.")
    return FileResponse(path, media_type="application/pdf", filename="enhanced_resume.pdf")

@app.get("/roles")
def get_roles():
    return {"roles": scorer.SUPPORTED_ROLES}

def _find(file_id: str) -> str:
    safe = "".join(c for c in file_id if c.isalnum() or c == "-")
    for ext in [".pdf", ".docx"]:
        p = os.path.join(UPLOAD_DIR, safe + ext)
        if os.path.exists(p):
            return p
    raise HTTPException(404, f"File not found for id: {file_id}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
