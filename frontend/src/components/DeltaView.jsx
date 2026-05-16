import { useState, useRef } from 'react';

const STATUS_STYLES = {
  changed: {
    bg: 'rgba(245,158,11,0.08)',
    border: 'rgba(245,158,11,0.3)',
    label: 'changed',
    color: 'var(--warning)',
  },
  added: {
    bg: 'rgba(16,185,129,0.08)',
    border: 'rgba(16,185,129,0.3)',
    label: 'added',
    color: 'var(--success-bright)',
  },
  removed: {
    bg: 'rgba(239,68,68,0.08)',
    border: 'rgba(239,68,68,0.3)',
    label: 'removed',
    color: 'var(--danger)',
  },
  unchanged: {
    bg: 'transparent',
    border: 'var(--nav-border)',
    label: 'unchanged',
    color: 'var(--text-tertiary)',
  },
};

export default function DeltaView() {
  const [delta, setDelta] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const file1Ref = useRef();
  const file2Ref = useRef();
  const [file1Name, setFile1Name] = useState(null);
  const [file2Name, setFile2Name] = useState(null);

  const handleCompare = async () => {
    const f1 = file1Ref.current?.files[0];
    const f2 = file2Ref.current?.files[0];
    if (!f1 || !f2) {
      setError('Please select both documents');
      return;
    }
    setLoading(true);
    setError(null);
    setDelta(null);
    const form = new FormData();
    form.append('file1', f1);
    form.append('file2', f2);
    form.append('doc_type', 'police_report');
    try {
      const res = await fetch(
        'http://localhost:8001/api/extract/delta',
        { method: 'POST', body: form });
      const data = await res.json();
      setDelta(data.delta);
      setSummary(data.summary);
    } catch (e) {
      setError('Comparison failed: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const filtered = delta ? Object.entries(delta).filter(
    ([_, v]) => filter === 'all' || v.status === filter
  ) : [];

  return (
    <div style={{ padding: '32px 40px',
      background: 'var(--surface-1)', minHeight: '100%' }}>

      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '10px', color: 'var(--accent)',
          fontFamily: 'var(--mono-font)', letterSpacing: '.12em',
          textTransform: 'uppercase', marginBottom: '8px' }}>
          Document comparison
        </div>
        <h2 style={{ fontSize: '22px', fontWeight: '500',
          color: '#f1f5f9', marginBottom: '6px' }}>
          Claim delta view
        </h2>
        <p style={{ fontSize: '13px',
          color: 'var(--text-tertiary)', lineHeight: '1.6' }}>
          Upload two versions of a document to see
          exactly what changed — field by field.
        </p>
      </div>

      {/* Upload row */}
      <div style={{ display: 'grid',
        gridTemplateColumns: '1fr 1fr auto',
        gap: '12px', marginBottom: '20px',
        alignItems: 'end' }}>
        {[
          { ref: file1Ref, label: 'Version 1 (original)',
            name: file1Name, setName: setFile1Name },
          { ref: file2Ref, label: 'Version 2 (updated)',
            name: file2Name, setName: setFile2Name },
        ].map((slot, i) => (
          <div key={i}>
            <div style={{ fontSize: '10px',
              color: 'var(--text-tertiary)',
              fontFamily: 'var(--mono-font)',
              textTransform: 'uppercase',
              letterSpacing: '.08em', marginBottom: '6px' }}>
              {slot.label}
            </div>
            <label style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              padding: '9px 12px',
              border: '0.5px dashed var(--accent-border)',
              borderRadius: '6px', cursor: 'pointer',
              background: 'var(--accent-bg)', fontSize: '12px',
              color: slot.name
                ? 'var(--accent)' : 'var(--text-tertiary)',
              fontFamily: 'var(--mono-font)',
            }}>
              <i className="ti ti-upload"
                style={{ fontSize: '14px' }}
                aria-hidden="true" />
              {slot.name || 'Select PDF'}
              <input type="file" accept=".pdf"
                ref={slot.ref}
                onChange={e => slot.setName(
                  e.target.files[0]?.name || null)}
                style={{ display: 'none' }} />
            </label>
          </div>
        ))}
        <button onClick={handleCompare} disabled={loading}
          style={{
            padding: '9px 20px',
            background: loading
              ? 'rgba(147,197,253,0.1)' : '#93c5fd',
            color: loading ? '#93c5fd' : '#0a1628',
            border: '0.5px solid #93c5fd',
            borderRadius: '6px', fontSize: '12px',
            fontWeight: '600', cursor: loading
              ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--mono-font)',
            whiteSpace: 'nowrap',
          }}>
          {loading ? 'Comparing...' : '⟷ Compare'}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div style={{ padding: '10px 14px', marginBottom: '16px',
          background: 'rgba(239,68,68,0.08)',
          border: '0.5px solid rgba(239,68,68,0.3)',
          borderRadius: '6px', fontSize: '12px',
          color: 'var(--danger)' }}>
          {error}
        </div>
      )}

      {/* Summary chips */}
      {summary && (
        <div style={{ display: 'flex', gap: '8px',
          marginBottom: '16px', flexWrap: 'wrap' }}>
          {[
            { key: 'all', label: 'All fields',
              count: Object.keys(delta).length },
            { key: 'changed', label: 'Changed',
              count: summary.changed },
            { key: 'added', label: 'Added',
              count: summary.added },
            { key: 'removed', label: 'Removed',
              count: summary.removed },
            { key: 'unchanged', label: 'Unchanged',
              count: summary.unchanged },
          ].map(f => (
            <button key={f.key} onClick={() => setFilter(f.key)}
              style={{
                padding: '5px 12px', borderRadius: '20px',
                border: `0.5px solid ${filter === f.key
                  ? 'var(--accent)' : 'var(--nav-border)'}`,
                background: filter === f.key
                  ? 'var(--accent-bg)' : 'transparent',
                color: filter === f.key
                  ? 'var(--accent)' : 'var(--text-tertiary)',
                fontSize: '11px', cursor: 'pointer',
                fontFamily: 'var(--mono-font)',
              }}>
              {f.label} ({f.count})
            </button>
          ))}
        </div>
      )}

      {/* Delta rows */}
      {filtered.length > 0 && (
        <div style={{ display: 'flex',
          flexDirection: 'column', gap: '6px' }}>
          {filtered.map(([field, info]) => {
            const s = STATUS_STYLES[info.status];
            return (
              <div key={field} style={{
                display: 'grid',
                gridTemplateColumns: '160px 1fr 1fr 80px',
                gap: '12px', alignItems: 'center',
                padding: '10px 14px',
                background: s.bg,
                border: `0.5px solid ${s.border}`,
                borderRadius: '8px',
              }}>
                <div style={{ fontSize: '10px',
                  color: 'var(--text-tertiary)',
                  fontFamily: 'var(--mono-font)',
                  textTransform: 'uppercase',
                  letterSpacing: '.06em' }}>
                  {field}
                </div>
                <div style={{ fontSize: '12px',
                  color: info.status === 'removed'
                    ? 'var(--danger)'
                    : 'var(--text-secondary)',
                  fontFamily: 'var(--mono-font)',
                  textDecoration: info.status === 'changed'
                    ? 'line-through' : 'none',
                  opacity: info.status === 'unchanged'
                    ? 0.5 : 1 }}>
                  {String(info.v1 || '—')}
                </div>
                <div style={{ fontSize: '12px',
                  color: info.status === 'added'
                    ? 'var(--success-bright)'
                    : info.status === 'changed'
                    ? '#f1f5f9' : 'var(--text-secondary)',
                  fontFamily: 'var(--mono-font)',
                  opacity: info.status === 'unchanged'
                    ? 0.5 : 1 }}>
                  {String(info.v2 || '—')}
                </div>
                <div style={{ fontSize: '10px',
                  color: s.color,
                  fontFamily: 'var(--mono-font)',
                  textAlign: 'right' }}>
                  {s.label}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Empty state */}
      {!delta && !loading && (
        <div style={{ textAlign: 'center', padding: '48px',
          color: 'var(--text-tertiary)', fontSize: '13px' }}>
          Select two versions of a document and click Compare
        </div>
      )}
    </div>
  );
}
