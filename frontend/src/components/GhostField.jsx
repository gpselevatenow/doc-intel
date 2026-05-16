import { useState, useEffect } from 'react';

export default function GhostField({
  field_id, predicted_value, confidence,
  basis, resolvedValue, isResolved,
}) {
  const [state, setState] = useState('ghost');
  // states: ghost | resolving | correct | wrong

  useEffect(() => {
    if (!isResolved) return;
    setState('resolving');
    const correct = resolvedValue
      ?.toLowerCase()
      .includes(predicted_value?.toLowerCase().slice(0, 8));
    setTimeout(() => {
      setState(correct ? 'correct' : 'wrong');
    }, 400);
  }, [isResolved, resolvedValue]);

  const conf = Math.round((confidence || 0.6) * 100);

  return (
    <div style={{
      padding: '9px 12px',
      borderRadius: '7px',
      borderLeft: `2px solid ${
        state === 'correct'
          ? 'var(--success-bright)'
          : state === 'wrong'
          ? 'var(--danger)'
          : 'rgba(147,197,253,0.3)'
      }`,
      background: state === 'correct'
        ? 'rgba(16,185,129,0.06)'
        : state === 'wrong'
        ? 'rgba(239,68,68,0.06)'
        : 'rgba(147,197,253,0.03)',
      marginBottom: '5px',
      transition: 'all 0.4s ease',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '3px',
      }}>
        <div style={{
          fontSize: '9px',
          color: 'var(--text-tertiary)',
          textTransform: 'uppercase',
          letterSpacing: '.08em',
          fontFamily: 'var(--mono-font)',
        }}>
          {field_id.replace(/_/g, ' ')}
        </div>
        <div style={{
          fontSize: '9px',
          fontFamily: 'var(--mono-font)',
          color: state === 'correct'
            ? 'var(--success-bright)'
            : state === 'wrong'
            ? 'var(--danger)'
            : 'rgba(147,197,253,0.6)',
        }}>
          {state === 'ghost'
            ? `predicted · ${conf}%`
            : state === 'resolving'
            ? 'resolving...'
            : state === 'correct'
            ? '✓ correct'
            : '≠ corrected'}
        </div>
      </div>
      <div style={{
        fontSize: '13px',
        fontFamily: 'var(--mono-font)',
        color: state === 'ghost'
          ? 'rgba(203,213,225,0.4)'
          : state === 'wrong'
          ? 'var(--danger)'
          : '#e2e8f0',
        fontStyle: state === 'ghost' ? 'italic' : 'normal',
        textDecoration: state === 'wrong' ? 'line-through' : 'none',
        transition: 'all 0.3s ease',
        minHeight: '18px',
      }}>
        {state === 'wrong' && resolvedValue
          ? resolvedValue
          : predicted_value}
      </div>
      {state === 'wrong' && resolvedValue && (
        <div style={{
          fontSize: '12px',
          color: '#e2e8f0',
          fontFamily: 'var(--mono-font)',
          marginTop: '4px',
        }}>
          → {resolvedValue}
        </div>
      )}
      {state === 'ghost' && (
        <div style={{
          fontSize: '9px',
          color: 'rgba(147,197,253,0.4)',
          marginTop: '3px',
          fontStyle: 'italic',
        }}>
          {basis}
        </div>
      )}
    </div>
  );
}
