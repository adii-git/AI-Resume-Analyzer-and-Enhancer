import React, { useEffect, useState } from 'react';

function color(s) {
  if (s >= 80) return 'var(--green)';
  if (s >= 60) return 'var(--accentl)';
  if (s >= 40) return 'var(--yellow)';
  return 'var(--red)';
}
function label(s) {
  if (s >= 80) return 'Excellent';
  if (s >= 60) return 'Good';
  if (s >= 40) return 'Fair';
  return 'Needs Work';
}

export default function ScoreGauge({ score, caption = 'ATS Score', size = 150 }) {
  const [shown, setShown] = useState(0);
  useEffect(() => {
    const end = Math.round(score), step = Math.max(Math.ceil(end / 40), 1);
    let cur = 0;
    const t = setInterval(() => {
      cur += step;
      if (cur >= end) { setShown(end); clearInterval(t); }
      else setShown(cur);
    }, 22);
    return () => clearInterval(t);
  }, [score]);

  const c   = color(shown);
  const deg = (shown / 100) * 360;
  const inner = size * 0.79;

  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{
        width: size, height: size, borderRadius: '50%',
        background: `conic-gradient(${c} ${deg}deg, var(--border) 0deg)`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        margin: '0 auto 8px', position: 'relative',
      }}>
        <div style={{
          position: 'absolute', width: inner, height: inner, borderRadius: '50%',
          background: 'var(--card)', display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', gap: 2,
        }}>
          <span style={{ fontWeight: 800, fontSize: size * 0.18, color: c, lineHeight: 1 }}>{shown}</span>
          <span style={{ fontSize: size * 0.07, color: 'var(--txt3)' }}>/100</span>
        </div>
      </div>
      <div style={{ fontWeight: 700, fontSize: '.88rem', color: c }}>{label(shown)}</div>
      <div style={{ color: 'var(--txt3)', fontSize: '.75rem', marginTop: 2 }}>{caption}</div>
    </div>
  );
}
