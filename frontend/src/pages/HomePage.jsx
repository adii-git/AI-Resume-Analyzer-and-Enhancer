import React from 'react';
import { Link } from 'react-router-dom';

const FEATURES = [
  { icon:'📄', title:'Smart Parsing',     desc:'Upload PDF or DOCX. Extracts name, skills, education, experience, projects using spaCy NLP + regex.' },
  { icon:'⚡', title:'ATS Score Engine',  desc:'Weighted formula: keyword match (40%) + skills (20%) + experience quality (20%) + formatting (20%).' },
  { icon:'🔍', title:'Keyword Gap',       desc:'See which JD keywords are present vs missing in your resume, with a visual match percentage.' },
  { icon:'🤖', title:'AI Enhancement',   desc:'GPT-4o-mini rewrites weak bullets into strong, quantified, action-verb-led statements.' },
  { icon:'📊', title:'Before vs After',  desc:'Side-by-side comparison with score improvement tracking after AI enhancement.' },
  { icon:'🏆', title:'Recruiter Mode',   desc:'Upload multiple resumes and rank them automatically against a single job description.' },
];

export default function HomePage() {
  return (
    <div>
      <div className="hero">
        <div className="hero-badge">🎓 For Job Seekers & Recruiters</div>
        <h1 className="hero-title">ATS-Aware AI<br />Resume Analyzer</h1>
        <p className="hero-sub">
          Upload your resume, paste a job description, and instantly get an ATS score,
          keyword gap analysis, AI-powered enhancements, and a downloadable improved PDF.
        </p>
        <div className="hero-btns">
          <Link to="/analyze" className="btn btn-p btn-lg">🔍 Analyze Resume</Link>
          <Link to="/enhance" className="btn btn-s btn-lg">✨ Enhance with AI</Link>
          <Link to="/compare" className="btn btn-s btn-lg">🏆 Compare Resumes</Link>
        </div>

        <div className="g4" style={{ maxWidth: 640, margin: '40px auto 0' }}>
          {[
            { v:'4',   d:'Score Components' },
            { v:'40%', d:'Keyword Weight'   },
            { v:'AI',  d:'Enhancement'      },
            { v:'PDF', d:'Download Ready'   },
          ].map(s => (
            <div key={s.d} className="sbox">
              <div className="sval">{s.v}</div>
              <div className="sdesc">{s.d}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="page" style={{ paddingTop: 0 }}>
        <hr className="divider" />
        <h2 style={{ textAlign:'center', fontWeight:800, fontSize:'1.4rem', marginBottom:28 }}>
          Everything You Need to Land the Interview
        </h2>
        <div className="feat-grid">
          {FEATURES.map(f => (
            <div key={f.title} className="feat">
              <div className="feat-icon">{f.icon}</div>
              <div className="feat-title">{f.title}</div>
              <div className="feat-desc">{f.desc}</div>
            </div>
          ))}
        </div>

        <hr className="divider" style={{ marginTop: 52 }} />
        <h2 style={{ textAlign:'center', fontWeight:800, fontSize:'1.4rem', marginBottom:28 }}>
          How the ATS Score is Calculated
        </h2>
        <div className="g2">
          {[
            { label:'Keyword Match',      pct:'40%', c:'var(--accentl)', desc:'TF-weighted presence of job description keywords in the resume text.' },
            { label:'Skills Relevance',   pct:'20%', c:'var(--purple)',  desc:'Overlap between your skills and role-specific keyword banks (SE, DS, DevOps, PM…).' },
            { label:'Experience Quality', pct:'20%', c:'var(--green)',   desc:'Action verb usage, quantified achievements, role count, absence of weak phrases.' },
            { label:'Formatting',         pct:'20%', c:'var(--yellow)',  desc:'Bullet usage, contact info completeness, word count, summary, section count.' },
          ].map(i => (
            <div key={i.label} className="card">
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:10 }}>
                <span style={{ fontWeight:700, color:i.c }}>{i.label}</span>
                <span style={{ fontWeight:800, fontSize:'1.1rem', color:i.c, background:`color-mix(in srgb,${i.c} 14%,transparent)`, padding:'2px 9px', borderRadius:'var(--r)' }}>{i.pct}</span>
              </div>
              <p style={{ color:'var(--txt2)', fontSize:'.84rem', lineHeight:1.6 }}>{i.desc}</p>
            </div>
          ))}
        </div>

        <div style={{ textAlign:'center', marginTop:48 }}>
          <Link to="/analyze" className="btn btn-p btn-lg">Get Started — It's Free →</Link>
        </div>
      </div>
    </div>
  );
}
