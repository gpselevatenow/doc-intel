import React, { useState, useEffect } from 'react';
import { Settings, Plus, Trash2, Database, Info } from 'lucide-react';

export default function ExtractionRules() {
  const [fields, setFields] = useState([]);
  const [newField, setNewField] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFields();
  }, []);

  const fetchFields = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8005/api/settings/fields');
      const data = await res.json();
      if (data.status === 'success') {
        setFields(data.fields);
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const addField = async (e) => {
    e.preventDefault();
    if (!newField.trim()) return;
    
    try {
      await fetch('http://localhost:8005/api/settings/fields', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ field_name: newField.trim() })
      });
      setNewField("");
      fetchFields();
    } catch (e) {
      console.error(e);
    }
  };

  const deleteField = async (fieldName) => {
    try {
      await fetch(`http://localhost:8005/api/settings/fields/${encodeURIComponent(fieldName)}`, {
        method: 'DELETE'
      });
      fetchFields();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="pane fade-in" style={{ padding: '2rem', flex: 1, overflowY: 'auto' }}>
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        
        <div style={{ marginBottom: '2rem' }}>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
            <Settings size={24} color="var(--accent)" /> Custom Extraction Rules
          </h2>
          <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem', lineHeight: 1.5 }}>
            The Generic Extraction Engine automatically flattens and extracts all tables it finds. 
            However, if you want to guarantee specific data points are explicitly searched for in 
            Police Reports or unstructured text, add them below.
          </p>
        </div>

        <div className="glass-card" style={{ marginBottom: '2rem' }}>
          <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Plus size={18} /> Add New Target Field
          </h3>
          <form onSubmit={addField} style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
            <input 
              type="text" 
              value={newField}
              onChange={(e) => setNewField(e.target.value)}
              placeholder="e.g., Investigating Officer, Road Conditions..."
              style={{ flex: 1, padding: '0.75rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'rgba(0,0,0,0.2)', color: 'white' }}
            />
            <button type="submit" className="btn-primary" disabled={!newField.trim()}>
              Add Field
            </button>
          </form>
        </div>

        <div className="glass-card">
          <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Database size={18} /> Active Target Fields
          </h3>
          
          {loading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading rules...</div>
          ) : fields.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
              <Info size={24} style={{ marginBottom: '0.5rem' }} />
              <div>No custom fields defined.</div>
              <div style={{ fontSize: '0.85rem' }}>The engine will still extract all generic table data automatically.</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '1rem' }}>
              {fields.map((field, idx) => (
                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem', background: 'rgba(0,0,0,0.3)', borderRadius: '4px', borderLeft: '3px solid var(--accent)' }}>
                  <span style={{ fontWeight: 500 }}>{field}</span>
                  <button 
                    onClick={() => deleteField(field)}
                    style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', padding: '0.2rem' }}
                    title="Delete Rule"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
