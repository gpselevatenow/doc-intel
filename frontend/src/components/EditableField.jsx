import React, { useState, useEffect } from 'react';
import { Edit2, AlertTriangle } from 'lucide-react';
import TypewriterValue from './TypewriterValue';

const EditableField = ({ value, delay = 0, speed = 80, resetKey = '', fieldName, docId, needsReview = false }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [currentValue, setCurrentValue] = useState(value);
  const [originalValue, setOriginalValue] = useState(value);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    setCurrentValue(value);
    setOriginalValue(value);
  }, [value]);

  const handleBlur = async () => {
    setIsEditing(false);
    if (currentValue !== originalValue) {
      try {
        const response = await fetch('http://localhost:8001/api/feedback/correction', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            doc_id: docId || "unknown_doc",
            field_name: fieldName,
            original_value: originalValue,
            new_value: currentValue
          })
        });
        if (response.ok) {
          setOriginalValue(currentValue);
        }
      } catch (err) {
        console.error("Failed to log correction:", err);
      }
    }
  };

  if (isEditing) {
    return (
      <input
        type="text"
        autoFocus
        style={{
          width: '100%',
          background: 'rgba(255,255,255,0.1)',
          border: '1px solid var(--accent)',
          color: 'white',
          padding: '0.2rem 0.5rem',
          borderRadius: '4px',
          fontFamily: 'inherit',
          fontSize: 'inherit'
        }}
        value={currentValue}
        onChange={(e) => setCurrentValue(e.target.value)}
        onBlur={handleBlur}
        onKeyDown={(e) => e.key === 'Enter' && handleBlur()}
      />
    );
  }

  const displayValue = (!currentValue || currentValue === 'Unknown' || currentValue === 'N/A' || currentValue === 'n/a')
    ? '—'
    : currentValue;

  const isMono = fieldName && (
    /plate|vin|report.?number|policy.?number/i.test(fieldName) ||
    /^\$[\d,]+/.test(currentValue || '')
  );

  const isLong = (currentValue || '').length > 120;

  return (
    <>
      <span
        className="editable-field"
        onClick={() => setIsEditing(true)}
        title="Click to correct this value"
        style={{
          cursor: 'pointer',
          display: '-webkit-box',
          WebkitLineClamp: expanded ? 'none' : 3,
          WebkitBoxOrient: 'vertical',
          overflow: expanded ? 'visible' : 'hidden',
          borderBottom: currentValue !== value ? '1px dashed var(--accent)' : '1px dashed transparent',
          transition: 'border-color 0.2s ease',
          fontFamily: isMono ? 'var(--font-mono, monospace)' : 'inherit',
          letterSpacing: isMono ? '0.06em' : 'inherit',
        }}
        onMouseEnter={(e) => e.currentTarget.style.borderBottom = '1px dashed rgba(255,255,255,0.3)'}
        onMouseLeave={(e) => e.currentTarget.style.borderBottom = currentValue !== value ? '1px dashed var(--accent)' : '1px dashed transparent'}
      >
        <TypewriterValue value={displayValue} delay={delay} speed={speed} resetKey={resetKey} />
        {needsReview && <AlertTriangle size={14} color="var(--warning)" style={{ marginLeft: '4px', verticalAlign: 'middle' }} title="Low Confidence: Please review" />}
        <Edit2 size={12} style={{ opacity: 0.3, marginLeft: '4px', verticalAlign: 'middle' }} />
      </span>
      {isLong && (
        <button
          onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
          style={{
            background: 'none', border: 'none', color: 'var(--accent)',
            cursor: 'pointer', fontSize: '11px', padding: '2px 0',
            display: 'block', marginTop: '4px'
          }}
        >
          {expanded ? '↑ Show less' : '↓ Show more'}
        </button>
      )}
    </>
  );
};

export default EditableField;
