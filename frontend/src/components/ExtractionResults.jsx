import React, { useState, useEffect, useMemo } from 'react';
import { Lightbulb, ArrowRightCircle, CheckCircle, AlertTriangle, Info, Plus, Trash2, RefreshCw, ThumbsUp, ThumbsDown, Search, X, Car, User, Eye, FileText, MapPin, Shield, AlertCircle, ShieldCheck } from 'lucide-react';
import EditableField from './EditableField';
import TypewriterValue from './TypewriterValue';
import { motion, AnimatePresence } from 'framer-motion';
import { AmbientRisk } from './AmbientRisk';

const Badge = () => (
  <span className="badge" title="High Confidence (Regex Validated)">
    <CheckCircle size={12} />
    High Confidence
  </span>
);

// ─── Shared helpers ──────────────────────────────────────────────────────────

const SectionHeader = ({ icon: Icon, title, count, color = 'var(--accent)' }) => (
  <div style={{
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    marginBottom: '1rem', paddingTop: '0.75rem',
    borderTop: '1px solid var(--border-color)'
  }}>
    <h3 style={{
      margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem',
      fontFamily: 'var(--font-mono, monospace)', fontSize: '10px',
      fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.12em',
      color: 'var(--text-muted)'
    }}>
      {Icon && <Icon size={14} color={color} />}
      {title}
    </h3>
    {count != null && (
      <span style={{
        background: 'rgba(255,255,255,0.06)', color: 'var(--text-muted)',
        fontSize: '11px', fontWeight: 700, padding: '0.15rem 0.5rem',
        borderRadius: '10px', border: '1px solid var(--border-color)',
        fontFamily: 'var(--font-mono, monospace)', letterSpacing: '0.04em'
      }}>{count}</span>
    )}
  </div>
);

const FieldRow = ({ label, value, onClick, unknown = false }) => {
  const isEmpty = !value || value === 'Unknown' || value === 'N/A';
  const isMono = /^(VIN|License Plate|Policy Number|Report Number)$/i.test(label) ||
    /^\$[\d,]+/.test(value || '');
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
      <span style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</span>
      <span
        className={onClick ? 'clickable-field' : ''}
        onClick={onClick}
        style={{
          fontSize: '0.88rem',
          color: isEmpty ? 'var(--text-muted)' : 'var(--text-main)',
          fontStyle: isEmpty ? 'italic' : 'normal',
          fontFamily: isMono && !isEmpty ? 'var(--font-mono, monospace)' : 'inherit',
          letterSpacing: isMono && !isEmpty ? '0.06em' : 'inherit',
        }}
      >
        {isEmpty ? '—' : value}
      </span>
    </div>
  );
};

const VehicleCard = ({ vehicle, index, onFieldClick }) => {
  const title = [vehicle.year, vehicle.make, vehicle.model].filter(x => x && x !== 'Unknown').join(' ') || 'Vehicle details';
  return (
    <div style={{
      background: 'var(--secondary-bg)', borderRadius: '10px',
      border: '1px solid var(--border-color)', overflow: 'hidden',
      marginBottom: '0.75rem'
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.75rem',
        padding: '0.75rem 1rem', background: 'rgba(255,255,255,0.04)',
        borderBottom: '1px solid var(--border-color)'
      }}>
        <span style={{
          background: 'var(--accent)', color: 'white', borderRadius: '6px',
          padding: '0.25rem 0.6rem', fontSize: '0.75rem', fontWeight: 700, whiteSpace: 'nowrap'
        }}>V{index + 1}</span>
        <span style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-main)' }}>{title}</span>
        {vehicle.color && vehicle.color !== 'Unknown' && (
          <span style={{
            fontSize: '0.75rem', color: 'var(--text-muted)',
            background: 'rgba(255,255,255,0.06)', padding: '0.15rem 0.5rem',
            borderRadius: '8px', border: '1px solid var(--border-color)'
          }}>{vehicle.color}</span>
        )}
        {vehicle.vin && vehicle.vin !== 'Unknown' && <Badge />}
      </div>
      <div style={{ padding: '0.875rem 1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem 1.5rem' }}>
        <FieldRow label="VIN" value={vehicle.vin} onClick={() => onFieldClick('vin')} />
        <FieldRow label="License Plate" value={vehicle.plate} onClick={() => onFieldClick('plate')} />
        <FieldRow label="Owner" value={vehicle.owner_name} onClick={() => onFieldClick('owner_name')} />
        <FieldRow label="Owner Address" value={vehicle.owner_address} onClick={() => onFieldClick('owner_address')} />
        <FieldRow label="Insurance Company" value={vehicle.insurance_company} onClick={() => onFieldClick('insurance_company')} />
        <FieldRow label="Policy Number" value={vehicle.policy_number} onClick={() => onFieldClick('policy_number')} />
        <FieldRow label="Damages" value={vehicle.damages} onClick={() => onFieldClick('damages')} />
        <FieldRow
          label="Towed"
          value={vehicle.towed && vehicle.towed !== 'Unknown'
            ? (vehicle.towing_company && vehicle.towing_company !== 'Unknown'
                ? `${vehicle.towed} — ${vehicle.towing_company}`
                : vehicle.towed)
            : null}
        />
      </div>
    </div>
  );
};

const roleColor = (role) => {
  const r = (role || '').toLowerCase();
  if (r.includes('operator') || r.includes('driver')) return { bg: 'rgba(59,130,246,0.15)', border: 'rgba(59,130,246,0.4)', text: '#60a5fa' };
  if (r.includes('passenger')) return { bg: 'rgba(156,163,175,0.1)', border: 'rgba(156,163,175,0.3)', text: '#9ca3af' };
  if (r.includes('pedestrian') || r.includes('bicyclist')) return { bg: 'rgba(251,146,60,0.15)', border: 'rgba(251,146,60,0.4)', text: '#fb923c' };
  if (r.includes('victim')) return { bg: 'rgba(167,139,250,0.15)', border: 'rgba(167,139,250,0.4)', text: '#a78bfa' };
  return { bg: 'rgba(255,255,255,0.04)', border: 'var(--border-color)', text: 'var(--text-muted)' };
};

const injuryColor = (injuries) => {
  const s = (injuries || '').toLowerCase();
  if (!injuries || s === 'unknown' || s === 'none reported') return 'var(--text-muted)';
  if (s.includes('fatal') || s.includes('serious')) return 'var(--danger)';
  if (s.includes('possible') || s.includes('complaint')) return 'var(--warning)';
  if (s.includes('no apparent') || s === 'none') return 'var(--success)';
  return 'var(--text-main)';
};

const PartyCard = ({ party, index, onFieldClick }) => {
  const colors = roleColor(party.role);
  const injColor = injuryColor(party.injuries);
  const hasInjury = party.injuries && party.injuries !== 'None reported' && party.injuries !== 'Unknown';
  return (
    <div style={{
      background: 'var(--secondary-bg)', borderRadius: '10px',
      border: `1px solid ${colors.border}`, overflow: 'hidden',
      marginBottom: '0.75rem'
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.75rem',
        padding: '0.75rem 1rem', background: colors.bg,
        borderBottom: `1px solid ${colors.border}`
      }}>
        <span style={{
          color: colors.text, background: colors.border, borderRadius: '6px',
          padding: '0.25rem 0.6rem', fontSize: '0.75rem', fontWeight: 700
        }}>{party.role || 'Person'}</span>
        <span style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-main)' }}>
          {party.name && party.name !== 'Unknown' ? party.name : `Person ${index + 1}`}
        </span>
        {hasInjury && (
          <span style={{
            marginLeft: 'auto', fontSize: '0.75rem', color: injColor,
            background: `${injColor}20`, padding: '0.2rem 0.6rem',
            borderRadius: '8px', border: `1px solid ${injColor}40`
          }}>{party.injuries}</span>
        )}
      </div>
      <div style={{ padding: '0.875rem 1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem 1.5rem' }}>
        <FieldRow label="Date of Birth" value={party.dob} onClick={() => onFieldClick('dob')} />
        <FieldRow label="Driver License #" value={party.license_number} onClick={() => onFieldClick('license_number')} />
        <div style={{ gridColumn: '1 / -1' }}>
          <FieldRow label="Address" value={party.address} onClick={() => onFieldClick('address')} />
        </div>
        <FieldRow label="Phone" value={party.phone !== 'Unknown' ? party.phone : null} />
        <FieldRow label="Substance" value={party.substance_involvement !== 'None reported' ? party.substance_involvement : null} />
        {party.transported && (
          <div style={{ gridColumn: '1 / -1' }}>
            <FieldRow label="Transported To" value={party.transported_to} onClick={() => onFieldClick('transported_to')} />
          </div>
        )}
        {party.citations && party.citations !== 'None' && (
          <div style={{ gridColumn: '1 / -1' }}>
            <FieldRow label="Citations" value={party.citations} onClick={() => onFieldClick('citations')} />
          </div>
        )}
      </div>
    </div>
  );
};

const WitnessCard = ({ witness, index, onFieldClick }) => (
  <div style={{
    background: 'var(--secondary-bg)', borderRadius: '10px',
    border: '1px solid var(--border-color)', padding: '0.75rem 1rem',
    marginBottom: '0.5rem', display: 'grid',
    gridTemplateColumns: '1fr 1fr', gap: '0.75rem 1.5rem'
  }}>
    <FieldRow label={`Witness ${index + 1}`} value={witness.name} onClick={() => onFieldClick('name')} />
    <FieldRow label="Phone" value={witness.phone !== 'Unknown' ? witness.phone : null} />
    <div style={{ gridColumn: '1 / -1' }}>
      <FieldRow label="Address" value={witness.address} onClick={() => onFieldClick('address')} />
    </div>
  </div>
);

function ReserveWarningBanner({ reserveWarning, reserveText }) {
  if (!reserveWarning) return null;
  return (
    <div style={{ animation: 'fieldLand 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0ms both' }}>
    <div
      style={{
        background: 'linear-gradient(135deg, rgba(239,68,68,0.15) 0%, rgba(239,68,68,0.08) 100%)',
        border: '1px solid var(--danger-border)',
        borderLeft: '4px solid var(--danger)',
        borderRadius: '10px',
        padding: '16px 20px',
        marginBottom: '20px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
        <span style={{ fontSize: '18px' }}>⚠️</span>
        <span style={{
          fontFamily: "'JetBrains Mono', 'Fira Code', 'Courier New', monospace",
          fontSize: '12px',
          fontWeight: '700',
          letterSpacing: '0.12em',
          color: 'var(--danger)',
          textTransform: 'uppercase',
        }}>Reserve Language Detected</span>
      </div>
      {reserveText && (
        <p style={{
          margin: '0 0 10px 28px',
          fontSize: '13px',
          color: 'var(--text-main)',
          fontStyle: 'italic',
          lineHeight: '1.5',
          borderLeft: '2px solid rgba(239,68,68,0.4)',
          paddingLeft: '12px',
        }}>
          "{reserveText}"
        </p>
      )}
      <p style={{
        margin: '0 0 0 28px',
        fontSize: '12px',
        color: 'var(--danger)',
        fontWeight: '600',
      }}>
        → Escalate to Claims Manager for reserve authorization
      </p>
    </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

const ExtractionResults = ({ type, data, docId, onFieldClick, isReprocessing, onReprocess, selectedField }) => {
  const [recommendations, setRecommendations] = useState('');
  const [customFields, setCustomFields] = useState([]);
  const [newField, setNewField] = useState('');
  const [feedbackGiven, setFeedbackGiven] = useState(null);
  const [auditModalField, setAuditModalField] = useState(null);

  const reserveText = useMemo(() => {
    if (!data?.reserve_warning) return null;
    if (data?.reserve_sentence) return data.reserve_sentence;
    // Fallback: scan summary for sentence containing reserve
    const summary = data?.summary || '';
    const sentences = summary.split(/[.!?]+/);
    const hit = sentences.find(s => /reserve/i.test(s) && s.trim().length > 10);
    return hit ? hit.trim() : null;
  }, [data]);

  const fieldScores = data?.accuracy_field_scores || {};
  const fv = (v) => (!v || v === 'Unknown' || v === 'N/A' || v === 'n/a') ? '—' : v;
  const confStyle = (fid) => {
    const conf = fieldScores?.[fid];
    if (conf === undefined || conf === null) return {};
    if (conf >= 80) return { borderLeft: '3px solid var(--success)', background: 'var(--success-bg)', borderRadius: '8px', padding: '10px 12px', marginBottom: '8px' };
    if (conf >= 50) return { borderLeft: '3px solid var(--warning)', background: 'var(--warning-bg)', borderRadius: '8px', padding: '10px 12px', marginBottom: '8px' };
    return { borderLeft: '3px solid var(--danger)', background: 'var(--danger-bg)', borderRadius: '8px', padding: '10px 12px', marginBottom: '8px' };
  };
  const renderFieldLabel = (label, fieldId) => {
    const conf = (fieldId && fieldId in fieldScores) ? fieldScores[fieldId] : null;
    const confColor = conf === null ? null : conf >= 80 ? 'var(--success)' : conf >= 50 ? 'var(--warning)' : 'var(--danger)';
    const confBg   = conf === null ? null : conf >= 80 ? 'rgba(16,185,129,0.12)' : conf >= 50 ? 'rgba(245,158,11,0.12)' : 'rgba(239,68,68,0.12)';
    const badge    = conf === null ? null : conf >= 80 ? 'AUTO-ACCEPTED' : conf >= 50 ? 'REVIEW REQUIRED' : 'ESCALATE';
    return (
      <div className="field-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
          <span>{label}</span>
          {conf !== null && (
            <span style={{ fontSize: '0.68rem', padding: '0.05rem 0.38rem', borderRadius: '8px', fontWeight: 700, background: confBg, color: confColor, lineHeight: 1.6 }}>{conf}%</span>
          )}
          {badge && (
            <span style={{ fontSize: '9px', color: confColor, fontFamily: 'var(--font-mono, monospace)', letterSpacing: '0.1em' }}>{badge}</span>
          )}
        </div>
        {fieldId && (
          <button onClick={() => setAuditModalField(fieldId)} title="View Audit Trail"
            style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer', color: 'var(--accent)' }}>
            <Search size={14} />
          </button>
        )}
      </div>
    );
  };

  const renderAuditModal = () => {
    if (!auditModalField) return null;
    const candidates = data.audit_trail ? data.audit_trail.filter(c => c.field_id === auditModalField) : [];
    return (
      <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '2rem', width: '80%', maxWidth: '800px', maxHeight: '80vh', overflowY: 'auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
            <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Search size={24} /> Audit Trail: {auditModalField}</h2>
            <button onClick={() => setAuditModalField(null)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}><X size={24} /></button>
          </div>
          {candidates.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>No audit trail data available for this field.</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <th style={{ padding: '0.5rem' }}>Rank</th>
                  <th style={{ padding: '0.5rem' }}>Value</th>
                  <th style={{ padding: '0.5rem' }}>Confidence</th>
                  <th style={{ padding: '0.5rem' }}>Strategy</th>
                </tr>
              </thead>
              <tbody>
                {candidates.sort((a, b) => b.confidence - a.confidence).map((c, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', background: i === 0 ? 'rgba(16,185,129,0.1)' : 'transparent' }}>
                    <td style={{ padding: '0.75rem 0.5rem' }}>{i + 1} {i === 0 && <CheckCircle size={14} style={{ color: 'var(--success)', verticalAlign: 'text-bottom' }} />}</td>
                    <td style={{ padding: '0.75rem 0.5rem', fontWeight: i === 0 ? 'bold' : 'normal' }}>{c.value}</td>
                    <td style={{ padding: '0.75rem 0.5rem' }}>{typeof c.confidence === 'number' ? c.confidence.toFixed(2) : c.confidence}</td>
                    <td style={{ padding: '0.75rem 0.5rem', fontFamily: 'monospace', fontSize: '0.85rem' }}>{c.source_strategy}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    );
  };

  if (!data) {
    return (
      <div className="fade-in" style={{ padding: '3rem', textAlign: 'center', background: 'var(--card-bg)', borderRadius: '12px', border: '1px solid var(--danger)' }}>
        <AlertTriangle size={48} style={{ marginBottom: '1rem', color: 'var(--danger)' }} />
        <h2 style={{ color: 'var(--danger)' }}>Extraction Failed</h2>
        <p style={{ color: 'var(--text-muted)' }}>The document could not be processed. This is usually caused by a backend server error or an invalid PDF.</p>
      </div>
    );
  }

  if (data.detail) {
    return (
      <div className="fade-in" style={{ padding: '3rem', textAlign: 'center', background: 'var(--card-bg)', borderRadius: '12px', border: '1px solid var(--danger)' }}>
        <AlertTriangle size={48} style={{ marginBottom: '1rem', color: 'var(--danger)' }} />
        <h2 style={{ color: 'var(--danger)' }}>Backend Error</h2>
        <p style={{ color: 'var(--text-muted)' }}>{typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)}</p>
      </div>
    );
  }

  const dynamic_fields = data.dynamic_fields || {};
  const review_flags = data.review_flags || {};

  useEffect(() => {
    if (docId) { fetchCustomFields(); setFeedbackGiven(null); }
  }, [docId]);

  const fetchCustomFields = async () => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/settings/fields/${encodeURIComponent(docId)}`);
      const json = await res.json();
      if (json.status === 'success') setCustomFields(json.fields);
    } catch (e) { console.error("Failed to fetch custom fields", e); }
  };

  const addField = async (e) => {
    e.preventDefault();
    if (!newField.trim() || !docId) return;
    try {
      await fetch('http://127.0.0.1:8000/api/settings/fields', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doc_id: docId, field_name: newField.trim() })
      });
      setNewField(''); fetchCustomFields();
    } catch (e) { console.error(e); }
  };

  const deleteField = async (fieldName) => {
    try {
      await fetch(`http://127.0.0.1:8000/api/settings/fields/${encodeURIComponent(docId)}/${encodeURIComponent(fieldName)}`, { method: 'DELETE' });
      fetchCustomFields();
    } catch (e) { console.error(e); }
  };

  const submitFeedback = async (action) => {
    try {
      await fetch('http://127.0.0.1:8000/api/feedback/rate', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doc_id: docId || 'unknown_doc', action })
      });
      setFeedbackGiven(action);
    } catch (e) { console.error("Failed to submit feedback", e); }
  };

  const riskLevel = data?.risk_level || 'low';

  const renderAccuracyBadge = () => {
    const score = data.accuracy_score || 0;
    const isHigh = score >= 90;
    const isMid = score >= 70 && score < 90;
    const color = isHigh ? 'var(--success-bright)' : isMid ? 'var(--warning)' : 'var(--danger)';
    const label = isHigh ? 'High confidence' : isMid ? 'Review recommended' : 'Escalation required';

    const riskColors = {
      low: { color: 'var(--success-bright)', label: 'Low risk' },
      medium: { color: 'var(--warning)', label: 'Medium risk' },
      high: { color: 'var(--danger)', label: 'High risk' },
    };
    const risk = riskColors[riskLevel] || riskColors.low;

    return (
      <div style={{ padding: '16px 20px', borderBottom: '0.5px solid var(--nav-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: '28px', fontWeight: '500', color, fontFamily: 'var(--mono-font)', lineHeight: 1 }}>
            {score.toFixed(1)}%
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginTop: '4px', fontFamily: 'var(--mono-font)' }}>
            Avg extraction confidence
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '10px',
            color: risk.color,
            fontFamily: 'var(--mono-font)',
            marginTop: '6px',
          }}>
            <div style={{
              width: '6px', height: '6px',
              borderRadius: '50%',
              background: risk.color,
            }} />
            {risk.label}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color, background: isHigh ? 'var(--success-bg)' : 'rgba(245,158,11,0.08)', padding: '6px 12px', borderRadius: '6px', fontFamily: 'var(--mono-font)', border: `0.5px solid ${isHigh ? 'var(--success-border)' : 'rgba(245,158,11,0.25)'}` }}>
          <ShieldCheck size={13} />
          {label}
        </div>
      </div>
    );
  };

  const renderInsights = () => {
    const chips = [];
    const actions = [];

    if (data.reserve_warning) chips.push({ label: 'Reserve language detected', color: 'var(--danger)', bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.25)', icon: '⚠' });
    if (data.subrogation && data.subrogation.toLowerCase().includes('investig')) chips.push({ label: 'Subrogation opportunity', color: 'var(--warning)', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.25)', icon: '⚖' });
    const opCount = (data.operators || []).length + (data.passengers || []).length + (data.pedestrians || []).length;
    if (opCount > 0) chips.push({ label: `${opCount} parties identified`, color: 'var(--accent)', bg: 'var(--accent-bg)', border: 'var(--accent-border)', icon: '◎' });
    const vCount = (data.vehicles || []).length;
    if (vCount > 0) chips.push({ label: `${vCount} vehicles`, color: 'var(--accent)', bg: 'var(--accent-bg)', border: 'var(--accent-border)', icon: '⬡' });
    if (data.coverage_a) chips.push({ label: 'Coverage A confirmed', color: 'var(--success-bright)', bg: 'var(--success-bg)', border: 'var(--success-border)', icon: '✓' });

    if (data.reserve_warning) actions.push(`Set reserve — ${data.settlement || 'amount TBD'}`);
    if (data.subrogation && data.subrogation.toLowerCase().includes('investig')) actions.push('File subrogation preservation letter');
    if (!data.agency || data.agency === 'Unknown') actions.push('Request agency supplement');
    if (opCount > 3) actions.push('Review liability across all parties');
    if (actions.length === 0) actions.push('Review extracted fields and submit to ClaimCenter');

    if (chips.length === 0 && actions.length === 0) return null;

    return (
      <div style={{ padding: '16px 20px', borderBottom: '0.5px solid var(--nav-border)' }}>
        {chips.length > 0 && (
          <div style={{ marginBottom: '14px' }}>
            <div style={{ fontSize: '9px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', fontFamily: 'var(--mono-font)', marginBottom: '8px' }}>Signals detected</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {chips.map((chip, i) => (
                <div key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '4px 10px', borderRadius: '20px', fontSize: '11px', color: chip.color, background: chip.bg, border: `0.5px solid ${chip.border}` }}>
                  <span style={{ fontSize: '10px' }}>{chip.icon}</span>
                  {chip.label}
                </div>
              ))}
            </div>
          </div>
        )}
        {actions.length > 0 && (
          <div>
            <div style={{ fontSize: '9px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', fontFamily: 'var(--mono-font)', marginBottom: '8px' }}>Next actions</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {actions.map((action, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', padding: '8px 12px', background: 'var(--surface-3)', borderRadius: '6px', fontSize: '12px', color: '#e2e8f0' }}>
                  <div style={{ width: '18px', height: '18px', borderRadius: '50%', background: 'var(--accent-bg)', border: '0.5px solid var(--accent-border)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '9px', color: 'var(--accent)', fontFamily: 'var(--mono-font)', flexShrink: 0, marginTop: '1px' }}>{i + 1}</div>
                  <span style={{ lineHeight: '1.4' }}>{action}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // ── ACORD render ─────────────────────────────────────────────────────────
  if (type === 'acord') {
    return (
      <div className="fade-in">
        <AmbientRisk riskLevel={riskLevel} />
        {renderAuditModal()}
        {renderAccuracyBadge()}
        {renderInsights()}
        <div className="glass-card">
          <SectionHeader icon={FileText} title="Extracted ACORD Data" />
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>Click any value below to edit and train the NLP engine.</p>
          <div className="grid-2">
            {[['Agency / Producer','agency'],['Insurance Carrier','carrier'],['Policy Number','policy_number'],['Named Insured','named_insured'],['Date of Loss','date_of_loss']].map(([label, fid]) => (
              <div key={fid}>{renderFieldLabel(label, fid)}<div className="field-value"><EditableField value={data[fid]} fieldName={fid} docId="acord_doc" needsReview={review_flags[fid]} /></div></div>
            ))}
          </div>
          <div style={{ marginTop: '1rem' }}>
            {renderFieldLabel('Description of Loss','description_of_loss')}
            <div className="field-value" style={{ whiteSpace: 'pre-wrap' }}><EditableField value={data.description_of_loss} fieldName="description_of_loss" docId="acord_doc" needsReview={review_flags['description_of_loss']} /></div>
          </div>
        </div>
        {dynamic_fields && Object.keys(dynamic_fields).length > 0 && (
          <div className="glass-card">
            <SectionHeader title="Custom Fields" />
            <div className="grid-2">
              {Object.entries(dynamic_fields).map(([key, val]) => (
                <div key={key}>{renderFieldLabel(key, key)}<div className="field-value"><EditableField value={val} fieldName={key} docId="dynamic_doc" needsReview={review_flags[`dynamic_${key}`]} /></div></div>
              ))}
            </div>
          </div>
        )}
        <div className="glass-card">
          <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}><FileTextIcon /> File Note Preview</h3>
          <textarea className="file-note" readOnly value={data.summary || ''} />
        </div>
      </div>
    );
  }

  // ── IA render ────────────────────────────────────────────────────────────
  if (type === 'ia') {
    return (
      <div className="fade-in">
        <AmbientRisk riskLevel={riskLevel} />
        {renderAuditModal()}
        <ReserveWarningBanner reserveWarning={data.reserve_warning} reserveText={reserveText} />
        {renderAccuracyBadge()}
        {renderInsights()}
        <div className="glass-card">
          <SectionHeader icon={FileText} title="Extracted Coverages & Estimates" />
          <div className="grid-2">
            {[['Cause of Loss','cause_of_loss'],['Settlement Estimate','settlement'],['Coverage A','coverage_a'],['Inspection Date','inspection_date'],['Inspection Firm','inspection_firm'],['Coverage B','coverage_b'],['Coverage C','coverage_c'],['Coverage D','coverage_d'],['Coverages / Policy Form','coverages'],['Subrogation Status','subrogation'],['Officials (Report Filed)','officials'],['Payment Summary','payment_summary']].map(([label, fid], index) => (
              <div key={fid} style={{ animation: `fieldLand 0.4s cubic-bezier(0.22,1,0.36,1) ${index * 400}ms both` }}>
                <motion.div
                  onClick={() => onFieldClick(fid)}
                  style={{ cursor: 'pointer', ...confStyle(fid) }}
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                >
                  {renderFieldLabel(label, fid)}
                  <div className="field-value" onClick={e => e.stopPropagation()}>
                    <EditableField value={data[fid]} delay={index * 400} speed={80} resetKey={docId} fieldName={fid} docId="ia_doc" needsReview={review_flags[fid]} />
                  </div>
                </motion.div>
              </div>
            ))}
          </div>
        </div>
        {Object.keys(dynamic_fields).length > 0 && (
          <div className="glass-card">
            <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>Custom Fields</h3>
            <div className="grid-2">
              {Object.entries(dynamic_fields).map(([key, val]) => (
                <div key={key}>{renderFieldLabel(key, key)}<div className="field-value"><EditableField value={val} fieldName={key} docId="dynamic_doc" needsReview={review_flags[`dynamic_${key}`]} /></div></div>
              ))}
            </div>
          </div>
        )}
        <div className="glass-card">
          <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>Adjuster Recommendations</h3>
          <textarea style={{ width: '100%', minHeight: '80px', padding: '0.75rem', borderRadius: '4px', background: 'rgba(0,0,0,0.2)', color: 'white', border: '1px solid var(--border-color)' }}
            placeholder="Type final recommendations here..." value={recommendations} onChange={e => setRecommendations(e.target.value)} />
        </div>
        <div className="glass-card">
          <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}><FileTextIcon /> File Note Preview</h3>
          <textarea className="file-note" readOnly value={recommendations.trim() ? `${data.summary || ''} Recommendations: ${recommendations.trim()}` : (data.summary || '')} />
        </div>
      </div>
    );
  }

  // ── Police / HSMV render ─────────────────────────────────────────────────
  const vehicles    = data.vehicles    || [];
  const parties     = data.parties     || [];
  const operators   = data.operators   || [];
  const passengers  = data.passengers  || [];
  const pedestrians = data.pedestrians || [];
  const witnesses   = data.witnesses   || [];

  return (
    <div className="fade-in">
      <AmbientRisk riskLevel={riskLevel} />
      {renderAuditModal()}
      {renderAccuracyBadge()}
      {renderInsights()}

      {/* ── Incident Summary ─────────────────────────────────────────── */}
      <div className="glass-card">
        <SectionHeader icon={MapPin} title="Incident Summary" />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div style={{ animation: 'fieldLand 0.4s cubic-bezier(0.22,1,0.36,1) 0ms both' }}>
            <motion.div
              onClick={() => onFieldClick('date_time')}
              style={{ cursor: 'pointer', ...confStyle('date_time') }}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
            >
              {renderFieldLabel('Date / Time', 'date_time')}
              <div className="field-value" onClick={e => e.stopPropagation()}><EditableField value={data.date_time} delay={0} speed={80} resetKey={docId} fieldName="date_time" docId="police_doc" needsReview={review_flags['date_time']} /></div>
            </motion.div>
          </div>
          <div style={{ animation: 'fieldLand 0.4s cubic-bezier(0.22,1,0.36,1) 400ms both' }}>
            <motion.div
              onClick={() => onFieldClick('location')}
              style={{ cursor: 'pointer', ...confStyle('location') }}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
            >
              {renderFieldLabel('Location', 'location')}
              <div className="field-value" onClick={e => e.stopPropagation()}><EditableField value={data.location} delay={400} speed={80} resetKey={docId} fieldName="location" docId="police_doc" needsReview={review_flags['location']} /></div>
            </motion.div>
          </div>
          <div style={{ animation: 'fieldLand 0.4s cubic-bezier(0.22,1,0.36,1) 800ms both' }}>
            <motion.div
              onClick={() => onFieldClick('weather')}
              style={{ cursor: 'pointer', ...confStyle('weather') }}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
            >
              {renderFieldLabel('Weather Conditions', 'weather')}
              <div className="field-value" onClick={e => e.stopPropagation()}><EditableField value={data.weather} delay={800} speed={80} resetKey={docId} fieldName="weather" docId="police_doc" needsReview={review_flags['weather']} /></div>
            </motion.div>
          </div>
          <div style={{ animation: 'fieldLand 0.4s cubic-bezier(0.22,1,0.36,1) 2000ms both' }}>
            <motion.div
              onClick={() => onFieldClick('accident_type')}
              style={{ cursor: 'pointer', ...confStyle('accident_type') }}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
            >
              {renderFieldLabel('Accident Type', 'accident_type')}
              <div className="field-value" onClick={e => e.stopPropagation()}><EditableField value={data.accident_type} delay={2000} speed={80} resetKey={docId} fieldName="accident_type" docId="police_doc" needsReview={review_flags['accident_type']} /></div>
            </motion.div>
          </div>
          <div style={{ animation: 'fieldLand 0.4s cubic-bezier(0.22,1,0.36,1) 3600ms both' }}>
            <motion.div
              onClick={() => onFieldClick('ems_agency')}
              style={{ cursor: 'pointer', ...confStyle('ems_agency') }}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
            >
              {renderFieldLabel('EMS Agency', 'ems_agency')}
              <div className="field-value" onClick={e => e.stopPropagation()}><EditableField value={data.ems_agency} delay={3600} speed={80} resetKey={docId} fieldName="ems_agency" docId="police_doc" needsReview={review_flags['ems_agency']} /></div>
            </motion.div>
          </div>
          <div style={{ animation: 'fieldLand 0.4s cubic-bezier(0.22,1,0.36,1) 1600ms both' }}>
            <motion.div
              onClick={() => onFieldClick('light_condition')}
              style={{ cursor: 'pointer', ...confStyle('light_condition') }}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
            >
              {renderFieldLabel('Light Condition', 'light_condition')}
              <div className="field-value" onClick={e => e.stopPropagation()}><EditableField value={data.light_condition} delay={1600} speed={80} resetKey={docId} fieldName="light_condition" docId="police_doc" needsReview={review_flags['light_condition']} /></div>
            </motion.div>
          </div>
          <div style={{ animation: 'fieldLand 0.4s cubic-bezier(0.22,1,0.36,1) 1200ms both' }}>
            <motion.div
              onClick={() => onFieldClick('road_surface')}
              style={{ cursor: 'pointer', ...confStyle('road_surface') }}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
            >
              {renderFieldLabel('Road Surface', 'road_surface')}
              <div className="field-value" onClick={e => e.stopPropagation()}><EditableField value={data.road_surface} delay={1200} speed={80} resetKey={docId} fieldName="road_surface" docId="police_doc" needsReview={review_flags['road_surface']} /></div>
            </motion.div>
          </div>
        </div>
      </div>

      {/* ── Agency & Investigation ───────────────────────────────────── */}
      <div className="glass-card">
        <SectionHeader icon={Shield} title="Agency & Investigation" />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div style={{ animation: 'fieldLand 0.4s cubic-bezier(0.22,1,0.36,1) 2400ms both' }}>
            <motion.div
              onClick={() => onFieldClick('agency')}
              style={{ cursor: 'pointer', ...confStyle('agency') }}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
            >
              {renderFieldLabel('Responding Agency', 'agency')}
              <div className="field-value" onClick={e => e.stopPropagation()}><EditableField value={data.agency} delay={2400} speed={80} resetKey={docId} fieldName="agency" docId="police_doc" needsReview={review_flags['agency']} /></div>
            </motion.div>
          </div>
          <div style={{ animation: 'fieldLand 0.4s cubic-bezier(0.22,1,0.36,1) 2800ms both' }}>
            <motion.div
              onClick={() => onFieldClick('officer')}
              style={{ cursor: 'pointer', ...confStyle('officer') }}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
            >
              {renderFieldLabel('Investigating Officer', 'officer')}
              <div className="field-value" onClick={e => e.stopPropagation()}><EditableField value={data.officer} delay={2800} speed={80} resetKey={docId} fieldName="officer" docId="police_doc" needsReview={review_flags['officer']} /></div>
            </motion.div>
          </div>
          <div style={{ animation: 'fieldLand 0.4s cubic-bezier(0.22,1,0.36,1) 3200ms both' }}>
            <motion.div
              onClick={() => onFieldClick('report_number')}
              style={{ cursor: 'pointer', ...confStyle('report_number') }}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
            >
              {renderFieldLabel('Report Number', 'report_number')}
              <div className="field-value" onClick={e => e.stopPropagation()}><EditableField value={data.report_number} delay={3200} speed={80} resetKey={docId} fieldName="report_number" docId="police_doc" needsReview={review_flags['report_number']} /></div>
            </motion.div>
          </div>
          {data.form_id && (
            <div>
              <span style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: '0.2rem' }}>Form / State</span>
              <span style={{ fontSize: '0.88rem', color: 'var(--text-main)' }}>
                {data.form_id} {data.form_state ? `(${data.form_state})` : ''} — {Math.round((data.form_confidence || 0) * 100)}% confidence
              </span>
            </div>
          )}
        </div>
      </div>

      {/* ── Involved Vehicles ────────────────────────────────────────── */}
      <div className="glass-card">
        <SectionHeader
          icon={Car}
          title="Involved Vehicles"
          count={vehicles.length ? `${vehicles.length} vehicle${vehicles.length !== 1 ? 's' : ''}` : null}
          color="#60a5fa"
        />
        {vehicles.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
            No vehicles extracted from this document.
          </div>
        ) : (
          vehicles.map((v, i) => (
            <div key={i} style={{ animation: `fieldLand 0.5s cubic-bezier(0.22, 1, 0.36, 1) ${i * 150 + 1500}ms both` }}>
              <VehicleCard vehicle={v} index={i} onFieldClick={(fieldName) => onFieldClick(`vehicles[${i}].${fieldName}`)} />
            </div>
          ))
        )}
      </div>

      {/* ── Operators & Passengers ───────────────────────────────────── */}
      <div className="glass-card">
        <SectionHeader
          icon={User}
          title="Operators & Passengers"
          count={(operators.length + passengers.length + pedestrians.length) > 0 ? `${operators.length + passengers.length + pedestrians.length} ${(operators.length + passengers.length + pedestrians.length) !== 1 ? 'people' : 'person'}` : null}
          color="#a78bfa"
        />
        {operators.length === 0 && passengers.length === 0 && pedestrians.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
            No parties identified in this document.
          </div>
        ) : (
          <>
            {operators.map((p, i) => (
              <div key={`op-${i}`} style={{ animation: `fieldLand 0.5s cubic-bezier(0.22, 1, 0.36, 1) ${i * 150 + 1500}ms both` }}>
                <PartyCard party={p} index={i} onFieldClick={(fieldName) => onFieldClick(`operators[${i}].${fieldName}`)} />
              </div>
            ))}
            {passengers.map((p, i) => (
              <div key={`pa-${i}`} style={{ animation: `fieldLand 0.5s cubic-bezier(0.22, 1, 0.36, 1) ${(operators.length + i) * 150 + 1500}ms both` }}>
                <PartyCard party={p} index={i} onFieldClick={(fieldName) => onFieldClick(`passengers[${i}].${fieldName}`)} />
              </div>
            ))}
            {pedestrians.map((p, i) => (
              <div key={`pe-${i}`} style={{ animation: `fieldLand 0.5s cubic-bezier(0.22, 1, 0.36, 1) ${(operators.length + passengers.length + i) * 150 + 1500}ms both` }}>
                <PartyCard party={p} index={i} onFieldClick={(fieldName) => onFieldClick(`pedestrians[${i}].${fieldName}`)} />
              </div>
            ))}
          </>
        )}
      </div>

      {/* ── Witnesses ────────────────────────────────────────────────── */}
      {witnesses.length > 0 && (
        <div className="glass-card">
          <SectionHeader
            icon={Eye}
            title="Witnesses"
            count={`${witnesses.length} witness${witnesses.length !== 1 ? 'es' : ''}`}
            color="#34d399"
          />
          {witnesses.map((w, i) => (
            <div key={i} style={{ animation: `fieldLand 0.5s cubic-bezier(0.22, 1, 0.36, 1) ${i * 150 + 1500}ms both` }}>
              <WitnessCard witness={w} index={i} onFieldClick={(fieldName) => onFieldClick(`witnesses[${i}].${fieldName}`)} />
            </div>
          ))}
        </div>
      )}

      {/* ── Contributing Factors ─────────────────────────────────────── */}
      {data.contributing_factors && data.contributing_factors !== 'Unknown' && (
        <div className="glass-card">
          <SectionHeader icon={AlertCircle} title="Contributing Factors" color="var(--warning)" />
          <div onClick={() => onFieldClick('contributing_factors')} style={{ cursor: 'pointer' }}>
            <div className="field-value" onClick={e => e.stopPropagation()}>
              <EditableField value={data.contributing_factors} fieldName="contributing_factors" docId="police_doc" needsReview={review_flags['contributing_factors']} />
            </div>
          </div>
        </div>
      )}

      {/* ── Property Damage ──────────────────────────────────────────── */}
      {data.property_damage && data.property_damage !== 'Unknown' && (
        <div className="glass-card">
          <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>Property Damage (Non-Vehicle)</h3>
          <div onClick={() => onFieldClick('property_damage')} style={{ cursor: 'pointer' }}>
            <div className="field-value" onClick={e => e.stopPropagation()}>
              <EditableField value={data.property_damage} fieldName="property_damage" docId="police_doc" needsReview={review_flags['property_damage']} />
            </div>
          </div>
        </div>
      )}

      {/* ── State Codes ──────────────────────────────────────────────── */}
      {data.state_codes && data.state_codes.length > 0 && (
        <div className="glass-card">
          <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>State Code Lookup</h3>
          {data.state_codes.map((code, i) => (
            <div key={i} style={{ background: 'rgba(239,68,68,0.1)', borderLeft: '4px solid var(--danger)', padding: '0.75rem', borderRadius: '4px', marginBottom: '0.5rem' }}>
              <strong>Code <span className="clickable-field" onClick={() => onFieldClick('code')}>{code.code}</span>:</strong> {code.description}
            </div>
          ))}
        </div>
      )}

      {/* ── Custom / Dynamic Fields ──────────────────────────────────── */}
      {Object.keys(dynamic_fields).length > 0 && (
        <div className="glass-card">
          <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>Custom Fields</h3>
          <div className="grid-2">
            {Object.entries(dynamic_fields).map(([key, val]) => (
              <div key={key}>{renderFieldLabel(key, key)}<div className="field-value"><EditableField value={val} fieldName={key} docId="dynamic_doc" needsReview={review_flags[`dynamic_${key}`]} /></div></div>
            ))}
          </div>
        </div>
      )}

      {/* ── Adjuster Recommendations ─────────────────────────────────── */}
      <div className="glass-card">
        <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>Adjuster Recommendations</h3>
        <textarea
          style={{ width: '100%', minHeight: '80px', padding: '0.75rem', borderRadius: '4px', background: 'rgba(0,0,0,0.2)', color: 'white', border: '1px solid var(--border-color)' }}
          placeholder="Type final recommendations here..."
          value={recommendations}
          onChange={e => setRecommendations(e.target.value)}
        />
      </div>

      {/* ── File Note ────────────────────────────────────────────────── */}
      <div className="glass-card">
        <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}><FileTextIcon /> File Note Preview</h3>
        <p className="field-label" style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between' }}>
          <span>Ready for copy-pasting.</span>
          <span style={{ color: 'var(--text-muted)' }}><Info size={14} style={{ verticalAlign: 'text-bottom' }} /> ClaimCenter Integration Pending</span>
        </p>
        <textarea className="file-note" readOnly
          value={recommendations.trim() ? `${data.summary || ''} Recommendations: ${recommendations.trim()}` : (data.summary || '')} />
      </div>

      {/* ── Add Custom Field ─────────────────────────────────────────── */}
      <div className="glass-card" style={{ border: '1px solid var(--accent)' }}>
        <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent)' }}>
          <Plus size={18} /> Add Custom Extraction Field
        </h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Force the engine to extract a specific field (e.g. "Ambulance Arrival Time") from this document.
        </p>
        <form onSubmit={addField} style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
          <input type="text" value={newField} onChange={e => setNewField(e.target.value)}
            placeholder="Type field name to extract..."
            style={{ flex: 1, padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'rgba(0,0,0,0.2)', color: 'white' }} />
          <button type="submit" className="btn-primary" disabled={!newField.trim()} style={{ padding: '0.5rem 1rem' }}>Add</button>
        </form>
        {customFields.length > 0 && (
          <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {customFields.map((field, i) => (
                <div key={i} style={{ background: 'rgba(255,255,255,0.1)', padding: '0.25rem 0.5rem', borderRadius: '16px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  {field}
                  <button onClick={() => deleteField(field)} style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', padding: 0 }}><Trash2 size={12} /></button>
                </div>
              ))}
            </div>
            <button className="btn-primary" onClick={onReprocess} disabled={isReprocessing}
              style={{ alignSelf: 'flex-start', background: 'var(--accent)', border: 'none' }}>
              {isReprocessing ? <><div className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></div> Rerunning...</> : <><RefreshCw size={16} /> Rerun Extraction with Custom Fields</>}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const FileTextIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
    <polyline points="14 2 14 8 20 8"></polyline>
    <line x1="16" y1="13" x2="8" y2="13"></line>
    <line x1="16" y1="17" x2="8" y2="17"></line>
    <polyline points="10 9 9 9 8 9"></polyline>
  </svg>
);

export default ExtractionResults;
