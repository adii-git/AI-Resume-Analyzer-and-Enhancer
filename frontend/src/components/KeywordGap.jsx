import React, { useState } from 'react';

export default function KeywordGap({ matched = [], missing = [] }) {
  const [all, setAll] = useState(false);
  const total  = matched.length + missing.length;
  const pct    = total > 0 ? Math.round((matched.length / total) * 100) : 0;
  const vMatch = all ? matched : matched.slice(0, 15);
  const vMiss  = all ? missing : missing.slice(0, 15);
  const c      = pct >= 60 ? 'var(--green)' : pct >= 40 ? 'var(--yellow)' : 'var(--red)';

  return (
    <div>
      {/* Summary */}
      <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 18, padding: '12px 16px', background: 'var(--bg2)', borderRadius: 'var(--r2)' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5, fontSize: '.78rem' }}>
            <span style={{ color: 'var(--green)', fontWeight: 600 }}>✓ {matched.length} matched</span>
            <span style={{ color: 'var(--red)',   fontWeight: 600 }}>✗ {missing.length} missing</span>
          </div>
          <div className="pbar" style={{ height: 10 }}>
            <div className="pfill" style={{ width: `${pct}%`, background: `linear-gradient(90deg,${c},var(--accentl))` }} />
          </div>
        </div>
        <span style={{ fontWeight: 800, fontSize: '1.3rem', color: c, minWidth: 50, textAlign: 'right' }}>{pct}%</span>
      </div>

      <div className="g2">
        <div>
          <p style={{ fontWeight: 700, color: 'var(--green)', fontSize: '.8rem', marginBottom: 8 }}>✅ Found in Resume</p>
          <div className="chips">
            {vMatch.map(k => <span key={k} className="chip cg">✓ {k}</span>)}
            {!vMatch.length && <span style={{ color: 'var(--txt3)', fontSize: '.78rem' }}>None detected</span>}
          </div>
        </div>
        <div>
          <p style={{ fontWeight: 700, color: 'var(--red)', fontSize: '.8rem', marginBottom: 8 }}>⚠️ Missing Keywords</p>
          <div className="chips">
            {vMiss.map(k => <span key={k} className="chip cr">✗ {k}</span>)}
            {!vMiss.length && <span style={{ color: 'var(--green)', fontSize: '.78rem' }}>🎉 No gaps found!</span>}
          </div>
        </div>
      </div>

      {(matched.length > 15 || missing.length > 15) && (
        <button className="btn btn-s btn-sm" style={{ marginTop: 14 }} onClick={() => setAll(!all)}>
          {all ? 'Show Less ↑' : `Show All (${total}) ↓`}
        </button>
      )}
    </div>
  );
}
