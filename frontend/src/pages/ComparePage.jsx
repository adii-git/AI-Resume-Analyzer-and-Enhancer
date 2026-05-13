import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';
import { uploadResume, compareResumes } from '../utils/api';
import ScoreGauge from '../components/ScoreGauge';

function MultiDrop({ uploads, setUploads }) {
  const [busy, setBusy] = useState(false);
  const onDrop = useCallback(async (files) => {
    setBusy(true);
    for (const file of files) {
      try {
        const d = await uploadResume(file, null);
        setUploads(prev => [...prev, { name: file.name, file_id: d.file_id, parsed: d.parsed }]);
        toast.success(`Uploaded: ${file.name}`);
      } catch (err) { toast.error(`${file.name}: ${err.message}`); }
    }
    setBusy(false);
  }, [setUploads]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, multiple: true, disabled: busy,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
  });

  return (
    <div>
      <div {...getRootProps()} className={`dz${isDragActive ? ' on' : ''}`} style={{ padding:'34px 20px' }}>
        <input {...getInputProps()} />
        <div className="dz-icon">{busy ? '⏳' : '📂'}</div>
        <p className="dz-text">{busy ? 'Uploading…' : <><strong>Drop multiple resumes</strong> or click to browse</>}</p>
        <p className="dz-hint">PDF & DOCX · Upload 2–10 resumes</p>
      </div>
      {uploads.length > 0 && (
        <div className="ul-list">
          {uploads.map((u, i) => (
            <div key={i} className="ul-item">
              <span className="ul-name">📄 {u.name}</span>
              <span className="ul-ok">✅ {u.parsed?.name || 'Parsed'} · {u.parsed?.skills?.length||0} skills</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Badge({ rank }) {
  const cls = rank===1?'gold':rank===2?'silver':rank===3?'bronze':'';
  return <span className={`rbadge ${cls}`}>{rank<=3?['🥇','🥈','🥉'][rank-1]:rank}</span>;
}

function MBar({ score, color }) {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:8 }}>
      <div className="pbar" style={{ flex:1 }}>
        <div className="pfill" style={{ width:`${score}%`, background:color }} />
      </div>
      <span style={{ fontWeight:700, fontSize:'.82rem', color, minWidth:28, textAlign:'right' }}>{Math.round(score)}</span>
    </div>
  );
}

export default function ComparePage() {
  const [uploads,  setUploads]  = useState([]);
  const [jd,       setJd]       = useState('');
  const [loading,  setLoading]  = useState(false);
  const [result,   setResult]   = useState(null);
  const [selected, setSelected] = useState(null);

  const run = async () => {
    if (uploads.length < 2) return toast.error('Upload at least 2 resumes.');
    if (jd.length < 30)     return toast.error('Job description too short.');
    setLoading(true); setResult(null); setSelected(null);
    try {
      const data = await compareResumes({ file_ids: uploads.map(u => u.file_id), job_description: jd });
      setResult(data); toast.success(`Ranked ${data.total} resumes!`);
    } catch (err) { toast.error(err.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="page">
      <div className="ph">
        <h1>Recruiter Mode</h1>
        <p>Upload multiple resumes and rank them automatically against a single job description.</p>
      </div>

      <div className="g2" style={{ marginBottom: 22 }}>
        <div className="card">
          <div className="card-title" style={{ justifyContent:'space-between' }}>
            <span>📂 Upload Resumes ({uploads.length})</span>
            {uploads.length > 0 && <button className="btn btn-s btn-sm" onClick={() => { setUploads([]); setResult(null); }}>Clear All</button>}
          </div>
          <MultiDrop uploads={uploads} setUploads={setUploads} />
        </div>
        <div className="card">
          <div className="card-title">💼 Job Description</div>
          <div className="fg">
            <label className="lbl">Paste the JD to rank against</label>
            <textarea className="textarea" rows={11} placeholder="Paste the full job description…" value={jd} onChange={e => setJd(e.target.value)} />
          </div>
          <button className="btn btn-p btn-full" onClick={run} disabled={loading || uploads.length < 2 || jd.length < 30}>
            {loading ? '⏳ Ranking…' : `🏆 Rank ${uploads.length} Resume${uploads.length!==1?'s':''}`}
          </button>
          {uploads.length < 2 && <p style={{ color:'var(--txt3)', fontSize:'.73rem', marginTop:8, textAlign:'center' }}>Upload at least 2 resumes to compare.</p>}
        </div>
      </div>

      {loading && <div className="card loading"><div className="spin" /><p>Analyzing and ranking {uploads.length} resumes…</p></div>}

      {result && !loading && (
        <>
          {/* Podium */}
          <div className="card" style={{ marginBottom:20 }}>
            <div className="card-title">🏆 Top Candidates</div>
            <div style={{ display:'flex', justifyContent:'center', alignItems:'flex-end', gap:20, padding:'20px 0' }}>
              {result.ranked[1] && (
                <div style={{ textAlign:'center' }}>
                  <ScoreGauge score={result.ranked[1].ats_score} caption={result.ranked[1].name||'#2'} size={110} />
                  <div style={{ marginTop:8 }}><Badge rank={2} /></div>
                </div>
              )}
              {result.ranked[0] && (
                <div style={{ textAlign:'center' }}>
                  <ScoreGauge score={result.ranked[0].ats_score} caption={result.ranked[0].name||'#1'} size={140} />
                  <div style={{ marginTop:8 }}><Badge rank={1} /></div>
                </div>
              )}
              {result.ranked[2] && (
                <div style={{ textAlign:'center' }}>
                  <ScoreGauge score={result.ranked[2].ats_score} caption={result.ranked[2].name||'#3'} size={110} />
                  <div style={{ marginTop:8 }}><Badge rank={3} /></div>
                </div>
              )}
            </div>
          </div>

          {/* Full table */}
          <div className="card" style={{ marginBottom:20 }}>
            <div className="card-title">📋 Full Rankings (click row to expand)</div>
            <table className="rtable">
              <thead><tr>
                <th>Rank</th><th>Candidate</th><th>ATS Score</th>
                <th>JD Similarity</th><th>Keyword Match</th><th>Top Skills</th>
              </tr></thead>
              <tbody>
                {result.ranked.map((r, i) => (
                  <tr key={r.file_id} onClick={() => setSelected(selected===i?null:i)}>
                    <td><Badge rank={i+1} /></td>
                    <td><span style={{ color:'var(--txt)', fontWeight:600 }}>{r.name||`Candidate ${i+1}`}</span></td>
                    <td><MBar score={r.ats_score} color={r.ats_score>=80?'var(--green)':r.ats_score>=60?'var(--accentl)':'var(--yellow)'} /></td>
                    <td><MBar score={r.similarity} color="var(--purple)" /></td>
                    <td><MBar score={r.breakdown?.keyword_match?.score||0} color="var(--accentl)" /></td>
                    <td><div className="chips">{(r.top_skills||[]).slice(0,4).map(s=><span key={s} className="chip cb" style={{fontSize:'.68rem',padding:'2px 8px'}}>{s}</span>)}</div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Expanded detail */}
          {selected !== null && result.ranked[selected] && (() => {
            const r = result.ranked[selected];
            const bd = r.breakdown || {};
            const cols = [
              { key:'keyword_match',      label:'Keyword Match',      color:'var(--accentl)' },
              { key:'skills_relevance',   label:'Skills Relevance',   color:'var(--purple)'  },
              { key:'experience_quality', label:'Experience Quality', color:'var(--green)'   },
              { key:'formatting',         label:'Formatting',         color:'var(--yellow)'  },
            ];
            return (
              <div className="card">
                <div className="card-title">
                  🔎 Detail — {r.name || `Candidate ${selected+1}`}
                  <button className="btn btn-s btn-sm" style={{ marginLeft:'auto' }} onClick={() => setSelected(null)}>✕ Close</button>
                </div>
                <div className="g2">
                  <div>
                    {cols.map(c => bd[c.key] ? (
                      <div key={c.key} style={{ marginBottom:14 }}>
                        <div style={{ display:'flex', justifyContent:'space-between', marginBottom:5, fontSize:'.84rem' }}>
                          <span style={{ color:'var(--txt2)' }}>{c.label}</span>
                          <span style={{ color:c.color, fontWeight:700 }}>{Math.round(bd[c.key].score)}/100</span>
                        </div>
                        <MBar score={bd[c.key].score} color={c.color} />
                      </div>
                    ) : null)}
                  </div>
                  <div>
                    <p style={{ color:'var(--txt3)', fontSize:'.72rem', marginBottom:8 }}>TOP SKILLS</p>
                    <div className="chips">{(r.top_skills||[]).map(s=><span key={s} className="chip cb">{s}</span>)}</div>
                    <div className="g2" style={{ marginTop:18 }}>
                      <div className="sbox"><div className="sval" style={{ fontSize:'1.5rem' }}>{Math.round(r.ats_score)}</div><div className="sdesc">ATS Score</div></div>
                      <div className="sbox"><div className="sval" style={{ fontSize:'1.5rem', color:'var(--purple)' }}>{r.similarity}%</div><div className="sdesc">Similarity</div></div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })()}
        </>
      )}

      {!result && !loading && (
        <div className="empty"><div className="empty-icon">🏆</div><p>Upload 2 or more resumes and a job description to rank candidates.</p></div>
      )}
    </div>
  );
}
