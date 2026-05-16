import { useEffect } from 'react';

const RISK_TOKENS = {
  low: {
    '--primary-bg': '#0a1628',
    '--secondary-bg': '#060e1d',
    '--accent': '#93c5fd',
    '--nav-bg': '#060e1d',
  },
  medium: {
    '--primary-bg': '#1a1208',
    '--secondary-bg': '#100c05',
    '--accent': '#fbbf24',
    '--nav-bg': '#100c05',
  },
  high: {
    '--primary-bg': '#1a0808',
    '--secondary-bg': '#100505',
    '--accent': '#f87171',
    '--nav-bg': '#100505',
  },
};

export function AmbientRisk({ riskLevel }) {
  useEffect(() => {
    const root = document.documentElement;
    const tokens = RISK_TOKENS[riskLevel] || RISK_TOKENS.low;
    Object.entries(tokens).forEach(([k, v]) => {
      root.style.setProperty(k, v);
    });
    return () => {
      Object.entries(RISK_TOKENS.low).forEach(([k, v]) => {
        root.style.setProperty(k, v);
      });
    };
  }, [riskLevel]);
  return null;
}
