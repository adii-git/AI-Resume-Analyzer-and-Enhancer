import React from 'react';

const META = {
  keyword_match     : { label: 'Keyword Match',      icon: '🔍', color: 'var(--accentl)' },
  skills_relevance  : { label: 'Skills Relevance',   icon: '🛠️', color: 'var(--purple)'  },
  experience_quality: { label: 'Experience Quality', icon: '💼', color: 'var(--green)'   },
  formatting        : { label: 'Formatting',         icon: '📐', color: 'var(--yellow)'  },
};

export default function ScoreBreakdown({ breakdown }) {
  if (!breakdown) return null;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      {Object.entries(breakdown).map(([key, val]) => {
        const m = META[key] || { label: key, icon: '📊', color: 'var(--accent)' };
        return (
          <div key={key}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
              <span style={{ fontWeight: 600, fontSize: '.88rem' }}>{m.icon} {m.label}</span>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                <span style={{ color: 'var(--txt3)', fontSize: '.73rem' }}>Weight {Math.round(val.weight * 100)}%</span>
                <span style={{ fontWeight: 800, color: m.color, fontSize: '.95rem', minWidth: 32, textAlign: 'right' }}>
                  {Math.round(val.score)}
                </span>
              </div>
            </div>
            <div className="pbar">
              <div className="pfill" style={{ width: `${val.score}%`, background: m.color }} />
            </div>
            {val.details && Object.keys(val.details).length > 0 && (
              <div style={{ marginTop: 5, padding: '6px 10px', background: 'var(--bg2)', borderRadius: 'var(--r)', fontSize: '.73rem', color: 'var(--txt3)', display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                {Object.entries(val.details).map(([k, v]) => (
                  <span key={k}>
                    <span style={{ color: 'var(--txt2)' }}>{k.replace(/_/g, ' ')}:</span>{' '}
                    {typeof v === 'number' ? (Number.isInteger(v) ? v : v.toFixed(2)) : String(v)}
                  </span>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
