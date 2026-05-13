import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import UploadZone from '../components/UploadZone';
import ScoreGauge from '../components/ScoreGauge';
import { enhanceResume, getRoles, downloadUrl } from '../utils/api';

function BulletComp({ origBullets, newBullets }) {
  return (
    <div className="cmp-grid" style={{ marginBottom: 16 }}>
      <div>
        <span className="cmp-lbl lbl-b">Before</span>
        <div className="cmp-text">{(origBullets||[]).map((b,i) => `• ${b}`).join('\n') || '—'}</div>
      </div>
      <div>
        <span className="cmp-lbl lbl-a">After</span>
        <div className="cmp-text" style={{ borderColor:'var(--greenborder)', borderWidth:1, borderStyle:'solid' }}>
          {(newBullets||[]).map((b,i) => `• ${b}`).join('\n') || '—'}
        </div>
      </div>
    </div>
  );
}

export default function EnhancePage() {
  const [fileId,   setFileId]   = useState(null);
  const [origParsed,setOrigParsed] = useState(null);
  const [jd,       setJd]       = useState('');
  const [role,     setRole]     = useState('General');
  const [roles,    setRoles]    = useState(['General']);
  const [loading,  setLoading]  = useState(false);
  const [result,   setResult]   = useState(null);
  const [tab,      setTab]      = useState('comparison');

  useEffect(() => { getRoles().then(setRoles).catch(() => {}); }, []);

  const handleUpload = d => { setFileId(d.file_id); setOrigParsed(d.parsed); };

  const run = async () => {
    if (!fileId)        return toast.error('Upload a resume first.');
    if (jd.length < 30) return toast.error('Job description too short (min 30 chars).');
    setLoading(true); setResult(null);
    try {
      const data = await enhanceResume({ file_id: fileId, job_description: jd, target_role: role });
      setResult(data); toast.success('Resume enhanced!');
    } catch (err) {
      toast.error(err.message);
    } finally { setLoading(false); }
  };

  const delta = result ? Math.round(result.enhanced_score - result.original_score) : 0;

  return (
    <div className="page">
      <div className="ph">
        <h1>AI Resume Enhancer</h1>
        <p>AI rewrites your bullets with impact-driven language and strong action verbs.</p>
      </div>

      <div className="g2" style={{ marginBottom: 22 }}>
        <div className="card">
          <div className="card-title">📄 Upload Resume</div>
          <UploadZone onUploaded={handleUpload} />
        </div>
        <div className="card">
          <div className="card-title">🎯 Settings</div>
          <div className="fg">
            <label className="lbl">Target Role</label>
            <select className="sel" value={role} onChange={e => setRole(e.target.value)}>
              {roles.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div className="fg">
            <label className="lbl">Job Description (for keyword tailoring)</label>
            <textarea className="textarea" rows={7} placeholder="Paste the target job description…" value={jd} onChange={e => setJd(e.target.value)} />
          </div>
          <button className="btn btn-p btn-full" onClick={run} disabled={loading || !fileId || jd.length < 30}>
            {loading ? '⏳ Enhancing with AI…' : '✨ Enhance Resume'}
          </button>
          <p style={{ color:'var(--txt3)', fontSize:'.73rem', marginTop:9, textAlign:'center' }}>
            Uses GPT-4o-mini if OPENAI_API_KEY is set, otherwise applies rule-based rewriting.
          </p>
        </div>
      </div>

      {loading && (
        <div className="card loading">
          <div className="spin" />
          <p>AI is enhancing your resume…</p>
          <p style={{ fontSize:'.76rem', color:'var(--txt3)' }}>May take 20–60 seconds for LLM calls.</p>
        </div>
      )}

      {result && !loading && (
        <>
          {/* Score bar */}
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-title">📈 Score Improvement</div>
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-around', padding:'18px 0' }}>
              <ScoreGauge score={result.original_score} caption="Original Score" size={120} />
              <div style={{ textAlign:'center' }}>
                <div style={{ fontWeight:800, fontSize:'2.2rem', color: delta >= 0 ? 'var(--green)' : 'var(--red)' }}>
                  {delta >= 0 ? '+' : ''}{delta}
                </div>
                <div style={{ color:'var(--txt3)', fontSize:'.76rem' }}>pts improvement</div>
                <div style={{ fontSize:'2rem', marginTop:12 }}>{delta >= 10 ? '🚀' : delta >= 5 ? '✅' : delta >= 0 ? '📈' : '⚠️'}</div>
              </div>
              <ScoreGauge score={result.enhanced_score} caption="Enhanced Score" size={120} />
            </div>
          </div>

          <div className="tabs">
            {[['comparison','⚡ Before vs After'],['improvements','✅ What Changed'],['download','📥 Download']].map(([k,l]) => (
              <button key={k} className={`tab${tab===k?' on':''}`} onClick={() => setTab(k)}>{l}</button>
            ))}
          </div>

          {tab === 'comparison' && (
            <div>
              {(result.enhanced_sections?.experience||[]).map((entry, i) => {
                const orig = origParsed?.experience?.[i];
                return (orig?.bullets?.length || entry.bullets?.length) ? (
                  <div key={i} className="card" style={{ marginBottom: 14 }}>
                    <div className="card-title">💼 {entry.title || `Experience ${i+1}`}{entry.company && <span style={{fontWeight:400,color:'var(--txt3)',marginLeft:8}}>{entry.company}</span>}</div>
                    <BulletComp origBullets={orig?.bullets||[]} newBullets={entry.bullets||[]} />
                  </div>
                ) : null;
              })}
              {(result.enhanced_sections?.projects||[]).map((proj, i) => {
                const orig = origParsed?.projects?.[i];
                return (orig?.description?.length || proj.description?.length) ? (
                  <div key={i} className="card" style={{ marginBottom: 14 }}>
                    <div className="card-title">🚀 {proj.title || `Project ${i+1}`}</div>
                    <BulletComp origBullets={orig?.description||[]} newBullets={proj.description||[]} />
                  </div>
                ) : null;
              })}
              {result.enhanced_sections?.summary && origParsed?.summary && (
                <div className="card">
                  <div className="card-title">📝 Professional Summary</div>
                  <BulletComp origBullets={[origParsed.summary]} newBullets={[result.enhanced_sections.summary]} />
                </div>
              )}
              {!result.enhanced_sections?.experience?.length && !result.enhanced_sections?.projects?.length && (
                <div className="empty"><div className="empty-icon">💡</div><p>No experience or project bullets were detected. Try a more detailed resume.</p></div>
              )}
            </div>
          )}

          {tab === 'improvements' && (
            <div className="card">
              <div className="card-title">✅ Improvements Made</div>
              <ul className="fbl">
                {(result.improvements||[]).map((tip, i) => (
                  <li key={i} className={`fbi${tip.startsWith('⚠') ? ' warn' : ' ok'}`}>
                    <span>{tip.startsWith('⚠') ? '⚠️' : '✅'}</span>
                    <span>{tip.replace(/^[✅⚠️]\s*/,'')}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {tab === 'download' && (
            <div className="card" style={{ textAlign:'center', padding:'44px' }}>
              <div style={{ fontSize:'3rem', marginBottom:16 }}>📥</div>
              <h3 style={{ fontWeight:800, fontSize:'1.3rem', marginBottom:10 }}>Your Enhanced Resume is Ready</h3>
              <p style={{ color:'var(--txt2)', marginBottom:24 }}>Download as a professional ATS-friendly PDF.</p>
              <a href={downloadUrl(fileId)} target="_blank" rel="noreferrer" className="btn btn-g btn-lg">
                ⬇️ Download Enhanced PDF
              </a>
              <p style={{ color:'var(--txt3)', fontSize:'.75rem', marginTop:14 }}>
                Score: <strong style={{color:'var(--txt)'}}>{result.original_score}</strong> → <strong style={{color:'var(--green)'}}>{result.enhanced_score}</strong>
              </p>
            </div>
          )}
        </>
      )}

      {!result && !loading && (
        <div className="empty"><div className="empty-icon">✨</div><p>Upload your resume and paste a job description to start AI enhancement.</p></div>
      )}
    </div>
  );
}
