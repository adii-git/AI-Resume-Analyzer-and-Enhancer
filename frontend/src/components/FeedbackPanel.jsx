import React, { useState } from 'react';

const TABS = [
  { key: 'skills',     icon: '🛠️', label: 'Skills'     },
  { key: 'experience', icon: '💼', label: 'Experience' },
  { key: 'projects',   icon: '🚀', label: 'Projects'   },
  { key: 'formatting', icon: '📐', label: 'Formatting' },
];

export default function FeedbackPanel({ feedback }) {
  const [active, setActive] = useState('skills');
  if (!feedback) return null;
  const tips = feedback[active] || [];

  return (
    <div>
      <div className="tabs">
        {TABS.map(({ key, icon, label }) => (
          <button key={key} className={`tab${active === key ? ' on' : ''}`} onClick={() => setActive(key)}>
            {icon} {label}
          </button>
        ))}
      </div>
      <ul className="fbl">
        {tips.map((tip, i) => {
          const isWarn = tip.startsWith('⚠') || tip.includes('missing') || tip.includes('no ') || tip.includes('No ') || tip.includes('Add');
          const isOk   = tip.startsWith('✅') || tip.toLowerCase().includes('great') || tip.toLowerCase().includes('good') || tip.toLowerCase().includes('strong') || tip.toLowerCase().includes('look');
          return (
            <li key={i} className={`fbi${isOk ? ' ok' : isWarn ? ' warn' : ''}`}>
              <span>{isOk ? '✅' : isWarn ? '⚠️' : '💡'}</span>
              <span>{tip.replace(/^[✅⚠️💡]\s*/, '')}</span>
            </li>
          );
        })}
        {!tips.length && (
          <li className="fbi ok"><span>✅</span><span>No issues found in this section.</span></li>
        )}
      </ul>
    </div>
  );
}
