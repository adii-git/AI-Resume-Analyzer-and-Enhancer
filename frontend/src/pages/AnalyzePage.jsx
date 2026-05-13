import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import UploadZone     from '../components/UploadZone';
import ScoreGauge     from '../components/ScoreGauge';
import ScoreBreakdown from '../components/ScoreBreakdown';
import KeywordGap     from '../components/KeywordGap';
import FeedbackPanel  from '../components/FeedbackPanel';
import { analyzeResume, getRoles } from '../utils/api';

export default function AnalyzePage() {
  const [fileId,  setFileId]  = useState(null);
  const [jd,      setJd]      = useState('');
  const [role,    setRole]    = useState('General');
  const [roles,   setRoles]   = useState(['General']);
  const [loading, setLoading] = useState(false);
  const [result,  setResult]  = useState(null);
  const [tab,     setTab]     = useState('score');

  useEffect(() => { getRoles().then(setRoles).catch(() => {}); }, []);

  const run = async () => {
    if (!fileId)        return toast.error('Upload a resume first.');
    if (jd.length < 30) return toast.error('Job description too short (min 30 chars).');
    setLoading(true); setResult(null);
    try {
      const data = await analyzeResume({ file_id: fileId, job_description: jd, target_role: role });
      setResult(data); toast.success('Analysis complete!');
    } catch (err) {
      toast.error(err.message);
    } finally { setLoading(false); }
  };

  return (
    <div className="page">
      <div className="ph">
        <h1>Resume Analyzer</h1>
        <p>Upload your resume and paste a job description to get a full ATS breakdown.</p>
      </div>

      <div className="g2" style={{ marginBottom: 22 }}>
        <div className="card">
          <div className="card-title">📄 Upload Resume</div>
          <UploadZone onUploaded={d => setFileId(d.file_id)} />
        </div>
        <div className="card">
          <div className="card-title">💼 Job Description</div>
          <div className="fg">
            <label className="lbl">Target Role</label>
            <select className="sel" value={role} onChange={e => setRole(e.target.value)}>
              {roles.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div className="fg">
            <label className="lbl">Paste Job Description</label>
            <textarea className="textarea" rows={8} placeholder="Paste the full job description…" value={jd} onChange={e => setJd(e.target.value)} />
          </div>
          <button className="btn btn-p btn-full" onClick={run} disabled={loading || !fileId || jd.length < 30}>
            {loading ? '⏳ Analyzing…' : '🔍 Analyze Resume'}
          </button>
        </div>
      </div>

      {loading && (
        <div className="card loading">
          <div className="spin" /><p>Running NLP analysis and computing ATS score…</p>
        </div>
      )}

      {result && !loading && (
        <>
          <div className="g3" style={{ marginBottom: 20 }}>
            {[
              { v: result.ats_score,        d: 'ATS Score / 100',    c: result.ats_score >= 60 ? 'var(--green)' : 'var(--red)' },
              { v: `${result.similarity_score}%`, d: 'JD Similarity', c: 'var(--accentl)' },
              { v: result.missing_keywords?.length || 0, d: 'Missing Keywords', c: 'var(--yellow)' },
            ].map(s => (
              <div key={s.d} className="sbox">
                <div className="sval" style={{ color: s.c }}>{s.v}</div>
                <div className="sdesc">{s.d}</div>
              </div>
            ))}
          </div>

          <div className="tabs">
            {[['score','📊 Score'],['keywords','🔍 Keywords'],['feedback','💡 Feedback'],['parsed','📋 Parsed']].map(([k,l]) => (
              <button key={k} className={`tab${tab===k?' on':''}`} onClick={() => setTab(k)}>{l}</button>
            ))}
          </div>

          {tab === 'score' && (
            <div className="g2">
              <div className="card" style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center' }}>
                <ScoreGauge score={result.ats_score} caption="ATS Score" />
                <p style={{ color:'var(--txt2)', fontSize:'.82rem', maxWidth:220, textAlign:'center', marginTop:16 }}>
                  {result.ats_score >= 80 ? 'Excellent! Well-optimized for ATS.' :
                   result.ats_score >= 60 ? 'Good. A few improvements can push you higher.' :
                   result.ats_score >= 40 ? 'Fair. Enhance keywords and experience bullets.' :
                   'Needs work. Use the AI Enhancer to improve your score.'}
                </p>
              </div>
              <div className="card">
                <div className="card-title">📊 Score Breakdown</div>
                <ScoreBreakdown breakdown={result.score_breakdown} />
              </div>
            </div>
          )}

          {tab === 'keywords' && (
            <div className="card">
              <div className="card-title">🔍 Keyword Gap Analysis</div>
              <KeywordGap matched={result.matched_keywords||[]} missing={result.missing_keywords||[]} />
            </div>
          )}

          {tab === 'feedback' && (
            <div className="card">
              <div className="card-title">💡 Section-wise Feedback</div>
              <FeedbackPanel feedback={result.feedback} />
            </div>
          )}

          {tab === 'parsed' && result.parsed && (
            <div className="card">
              <div className="card-title">📋 Parsed Resume Data</div>
              <div className="g2">
                <div>
                  <p style={{ color:'var(--txt3)', fontSize:'.72rem', marginBottom:3 }}>NAME</p>
                  <p style={{ fontWeight:600, marginBottom:12 }}>{result.parsed.name || '—'}</p>
                  <p style={{ color:'var(--txt3)', fontSize:'.72rem', marginBottom:3 }}>CONTACT</p>
                  <p style={{ color:'var(--txt2)', fontSize:'.83rem', marginBottom:12 }}>
                    {[result.parsed.email, result.parsed.phone, result.parsed.linkedin, result.parsed.github].filter(Boolean).join(' · ') || '—'}
                  </p>
                  <p style={{ color:'var(--txt3)', fontSize:'.72rem', marginBottom:3 }}>SKILLS ({result.parsed.skills?.length || 0})</p>
                  <div className="chips">{(result.parsed.skills||[]).slice(0,20).map(s => <span key={s} className="chip cb">{s}</span>)}</div>
                </div>
                <div>
                  <p style={{ color:'var(--txt3)', fontSize:'.72rem', marginBottom:6 }}>EXPERIENCE ({result.parsed.experience?.length || 0} roles)</p>
                  {(result.parsed.experience||[]).map((e,i) => (
                    <div key={i} style={{ padding:'7px 11px', background:'var(--bg2)', borderRadius:'var(--r)', marginBottom:7, fontSize:'.83rem' }}>
                      <strong>{e.title}</strong>{e.company && <span style={{color:'var(--txt3)'}}> · {e.company}</span>}
                    </div>
                  ))}
                  <p style={{ color:'var(--txt3)', fontSize:'.72rem', marginBottom:6, marginTop:10 }}>EDUCATION</p>
                  {(result.parsed.education||[]).map((e,i) => (
                    <div key={i} style={{ padding:'7px 11px', background:'var(--bg2)', borderRadius:'var(--r)', marginBottom:7, fontSize:'.83rem' }}>
                      <strong>{e.degree}</strong>{e.institution && <span style={{color:'var(--txt3)'}}> · {e.institution}</span>}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {!result && !loading && (
        <div className="empty"><div className="empty-icon">📊</div><p>Upload a resume and paste a job description to see your ATS analysis.</p></div>
      )}
    </div>
  );
}
