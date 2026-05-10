import React, { useState, useEffect } from 'react';
import { Edit2 } from 'lucide-react';

const EditableField = ({ value, fieldName, docId }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [currentValue, setCurrentValue] = useState(value);
  const [originalValue, setOriginalValue] = useState(value);

  useEffect(() => {
    setCurrentValue(value);
    setOriginalValue(value);
  }, [value]);

  const handleBlur = async () => {
    setIsEditing(false);
    if (currentValue !== originalValue) {
      try {
        const response = await fetch('http://localhost:8000/api/feedback/correction', {
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
          setOriginalValue(currentValue); // update baseline
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

  return (
    <span 
      className="editable-field" 
      onClick={() => setIsEditing(true)}
      title="Click to correct this value"
      style={{ 
        cursor: 'pointer', 
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.25rem',
        borderBottom: currentValue !== value ? '1px dashed var(--accent)' : '1px dashed transparent',
        transition: 'border-color 0.2s ease'
      }}
      onMouseEnter={(e) => e.currentTarget.style.borderBottom = '1px dashed rgba(255,255,255,0.3)'}
      onMouseLeave={(e) => e.currentTarget.style.borderBottom = currentValue !== value ? '1px dashed var(--accent)' : '1px dashed transparent'}
    >
      {currentValue} <Edit2 size={12} style={{ opacity: 0.3 }} />
    </span>
  );
};

export default EditableField;
