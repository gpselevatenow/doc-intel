import React, { useState, useEffect } from 'react';
import { Lightbulb, ArrowRightCircle, CheckCircle, AlertTriangle, Info, Plus, Trash2 } from 'lucide-react';
import EditableField from './EditableField';

const Badge = () => (
  <span className="badge" title="High Confidence (Regex Validated)">
    <CheckCircle size={12} />
    High Confidence
  </span>
);

const ExtractionResults = ({ type, data, docId, onFieldClick }) => {
  const [recommendations, setRecommendations] = useState('');
  const [customFields, setCustomFields] = useState([]);
  const [newField, setNewField] = useState('');

  useEffect(() => {
    if (docId) {
      fetchCustomFields();
    }
  }, [docId]);

  const fetchCustomFields = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/settings/fields/${encodeURIComponent(docId)}`);
      const json = await res.json();
      if (json.status === 'success') {
        setCustomFields(json.fields);
      }
    } catch (e) {
      console.error("Failed to fetch custom fields", e);
    }
  };

  const addField = async (e) => {
    e.preventDefault();
    if (!newField.trim() || !docId) return;
    try {
      await fetch('http://localhost:8000/api/settings/fields', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doc_id: docId, field_name: newField.trim() })
      });
      setNewField('');
      fetchCustomFields();
      alert(`Added '${newField}'. Please click 'Run Extraction' again in the sidebar to populate this field.`);
    } catch (e) {
      console.error(e);
    }
  };

  const deleteField = async (fieldName) => {
    try {
      await fetch(`http://localhost:8000/api/settings/fields/${encodeURIComponent(docId)}/${encodeURIComponent(fieldName)}`, {
        method: 'DELETE'
      });
      fetchCustomFields();
    } catch (e) {
      console.error(e);
    }
  };

  const score = data.accuracy_score || 0;
  let scoreColor = "var(--success)";
  let scoreText = "High Confidence";
  if (score < 90 && score >= 70) {
    scoreColor = "var(--warning)";
    scoreText = "Review Recommended";
  } else if (score < 70) {
    scoreColor = "var(--danger)";
    scoreText = "ESCALATION REQUIRED: Low Data Extraction Confidence";
  }

  const renderAccuracyBadge = () => (
    <div style={{ marginBottom: '1rem', background: 'var(--card-bg)', border: `1px solid ${scoreColor}`, borderRadius: '8px', overflow: 'hidden' }}>
      <div style={{ padding: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color: scoreColor }}>
            {score >= 90 ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
            Extraction Accuracy: {score.toFixed(1)}%
          </h3>
          <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>{scoreText}</p>
        </div>
        {score < 70 && (
          <button className="btn-primary" style={{ background: 'var(--danger)', border: 'none' }}>
            Escalate to Supervisor
          </button>
        )}
      </div>
      {data.accuracy_reasons && data.accuracy_reasons.length > 0 && (
        <details style={{ padding: '0.5rem 1rem', background: 'rgba(0,0,0,0.2)', borderTop: `1px solid ${scoreColor}` }}>
          <summary style={{ cursor: 'pointer', fontSize: '0.85rem', color: 'var(--text-muted)' }}>Why this score?</summary>
          <ul style={{ margin: '0.5rem 0 0 0', paddingLeft: '1.5rem', fontSize: '0.8rem', color: 'var(--text-main)' }}>
            {data.accuracy_reasons.map((reason, idx) => (
              <li key={idx} style={{ color: reason.startsWith('Found') ? 'var(--success)' : 'var(--danger)', marginBottom: '0.25rem' }}>{reason}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );

  // --- Insights & Next Best Action Engine ---
  let insights = [];
  let nextActions = [];

  if (type === 'ia') {
    if (data.summary && data.summary.includes("WARNING: RESERVE INCLUDED")) {
      insights.push("High severity claim with explicit reserve request detected.");
      nextActions.push("Escalate to Claims Manager for reserve authorization.");
    } else {
      insights.push("Standard property claim layout detected.");
      nextActions.push("Proceed to standard settlement workflow.");
    }
    
    if (data.subrogation && data.subrogation.toLowerCase() === 'yes') {
      insights.push("Third-party liability identified.");
      nextActions.push("Initiate subrogation investigation against third party.");
    }
  } else if (type === 'acord') {
    if (data.description_of_loss && data.description_of_loss.toLowerCase().includes('fire')) {
      insights.push("Severe property loss (Fire) indicated in description.");
      nextActions.push("Assign to Large Loss Adjuster team immediately.");
    } else {
      insights.push("Standard ACORD Loss Notice parsed.");
      nextActions.push("Verify policy coverage limits for the reported Date of Loss.");
    }
  } else {
    const hasDui = data.state_codes && data.state_codes.some(c => c.code === '9-2' || c.description.includes('DUI'));
    if (hasDui) {
      insights.push("Severe traffic violation (DUI) detected in State Codes.");
      nextActions.push("Flag claim for SIU (Special Investigation Unit) review.");
    }
    
    if (data.ems && data.ems.toLowerCase() === 'yes') {
      insights.push("Medical transport (EMS) confirmed on scene.");
      nextActions.push("Initiate Bodily Injury (BI) workflow and request medical records.");
    }
    
    if (data.vehicles && data.vehicles.length > 2) {
      insights.push(`Multi-vehicle collision (${data.vehicles.length} vehicles involved).`);
      if (!hasDui) nextActions.push("Review liability apportionment across all drivers.");
    }
    
    if (insights.length === 0) {
      insights.push("Standard single or dual-vehicle incident reported with no severe flags.");
      nextActions.push("Proceed with standard auto-damage appraisal.");
    }
  }

  const renderInsights = () => (
    <div className="insight-container fade-in">
      <div className="insight-card">
        <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--success)' }}>
          <Lightbulb size={20} /> Document Insights
        </h3>
        <ul style={{ margin: 0, paddingLeft: '1.5rem', color: 'var(--text-main)' }}>
          {insights.map((ins, idx) => <li key={idx} style={{ marginBottom: '0.5rem' }}>{ins}</li>)}
        </ul>
      </div>
      
      <div className="action-card">
        <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--danger)' }}>
          <ArrowRightCircle size={20} /> Next Best Action
        </h3>
        <ul style={{ margin: 0, paddingLeft: '1.5rem', color: 'var(--text-main)' }}>
          {nextActions.map((act, idx) => <li key={idx} style={{ marginBottom: '0.5rem' }}><strong>{act}</strong></li>)}
        </ul>
      </div>
    </div>
  );

  // --- Render Payload ---
  if (type === 'acord') {
    return (
      <div className="fade-in">
        {renderAccuracyBadge()}
        {renderInsights()}

        <div className="glass-card">
          <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
            Extracted ACORD Data
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>Click any value below to edit it and train the NLP engine.</p>
          <div className="grid-2">
            <div>
              <div className="field-label">Agency / Producer</div>
              <div className="field-value"><EditableField value={data.agency} fieldName="agency" docId="acord_doc" needsReview={data.review_flags?.['agency']} /></div>
            </div>
            <div>
              <div className="field-label">Insurance Carrier</div>
              <div className="field-value"><EditableField value={data.carrier} fieldName="carrier" docId="acord_doc" needsReview={data.review_flags?.['carrier']} /></div>
            </div>
            <div>
              <div className="field-label">Policy Number</div>
              <div className="field-value"><EditableField value={data.policy_number} fieldName="policy_number" docId="acord_doc" needsReview={data.review_flags?.['policy_number']} /></div>
            </div>
            <div>
              <div className="field-label">Named Insured</div>
              <div className="field-value"><EditableField value={data.named_insured} fieldName="named_insured" docId="acord_doc" needsReview={data.review_flags?.['named_insured']} /></div>
            </div>
            <div>
              <div className="field-label">Date of Loss</div>
              <div className="field-value"><EditableField value={data.date_of_loss} fieldName="date_of_loss" docId="acord_doc" needsReview={data.review_flags?.['date_of_loss']} /></div>
            </div>
          </div>
          <div style={{ marginTop: '1rem' }}>
            <div className="field-label">Description of Loss</div>
            <div className="field-value" style={{ whiteSpace: 'pre-wrap' }}><EditableField value={data.description_of_loss} fieldName="description_of_loss" docId="acord_doc" needsReview={data.review_flags?.['description_of_loss']} /></div>
          </div>
        </div>

        {data.dynamic_fields && Object.keys(data.dynamic_fields).length > 0 && (
          <div className="glass-card" style={{ marginBottom: '1rem' }}>
            <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
              Extracted Table Data & Custom Fields
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>Fields extracted automatically by the generic NLP engine.</p>
            <div className="grid-2">
              {Object.entries(data.dynamic_fields).map(([key, val], idx) => (
                <div key={idx}>
                  <div className="field-label">{key}</div>
                  <div className="field-value"><EditableField value={val} fieldName={key} docId="dynamic_doc" needsReview={data.review_flags?.[`dynamic_${key}`]} /></div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="glass-card">
          <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileTextIcon /> File Note Preview
          </h3>
          <p className="field-label" style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between' }}>
            <span>Ready for copy-pasting.</span>
            <span style={{ color: 'var(--text-muted)' }}><Info size={14} style={{ verticalAlign: 'text-bottom' }}/> ClaimCenter Integration Pending</span>
          </p>
          <textarea 
            className="file-note" 
            readOnly 
            value={data.summary} 
          />
        </div>
      </div>
    );
  }

  if (type === 'ia') {
    return (
      <div className="fade-in">
        {renderAccuracyBadge()}
        {renderInsights()}

        <div className="glass-card">
          <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
            Extracted Coverages & Estimates
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>Click any value below to highlight it in the original document.</p>
          <div className="grid-2">
            <div>
              <div className="field-label">Cause of Loss</div>
              <div className="field-value clickable-field" onClick={() => onFieldClick('cause_of_loss')}>{data.cause_of_loss}</div>
            </div>
            <div>
              <div className="field-label">Settlement Estimate <Badge /></div>
              <div className="field-value clickable-field" onClick={() => onFieldClick('settlement')}>{data.settlement}</div>
            </div>
            <div>
              <div className="field-label">Coverage A</div>
              <div className="field-value clickable-field" onClick={() => onFieldClick('coverage_a')}>{data.coverage_a}</div>
            </div>
            <div>
              <div className="field-label">Coverage B</div>
              <div className="field-value clickable-field" onClick={() => onFieldClick('coverage_b')}>{data.coverage_b}</div>
            </div>
            <div>
              <div className="field-label">Coverage C</div>
              <div className="field-value clickable-field" onClick={() => onFieldClick('coverage_c')}>{data.coverage_c}</div>
            </div>
            <div>
              <div className="field-label">Coverage D</div>
              <div className="field-value clickable-field" onClick={() => onFieldClick('coverage_d')}>{data.coverage_d}</div>
            </div>
            <div>
              <div className="field-label">Subrogation Status</div>
              <div className="field-value clickable-field" onClick={() => onFieldClick('subrogation')}>{data.subrogation}</div>
            </div>
          </div>
        </div>

        <div className="glass-card" style={{ marginBottom: '1rem' }}>
          <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
            Adjuster Recommendations
          </h3>
          <textarea 
            style={{ width: '100%', minHeight: '80px', padding: '0.75rem', borderRadius: '4px', background: 'rgba(0,0,0,0.2)', color: 'white', border: '1px solid var(--border-color)' }}
            placeholder="Type final recommendations here..."
            value={recommendations}
            onChange={(e) => setRecommendations(e.target.value)}
          />
        </div>

        <div className="glass-card">
          <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileTextIcon /> File Note Preview
          </h3>
          <p className="field-label" style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between' }}>
            <span>Ready for copy-pasting.</span>
            <span style={{ color: 'var(--text-muted)' }}><Info size={14} style={{ verticalAlign: 'text-bottom' }}/> ClaimCenter Integration Pending</span>
          </p>
          <textarea 
            className="file-note" 
            readOnly 
            value={recommendations.trim() ? `${data.summary} Recommendations: ${recommendations.trim()}` : data.summary} 
          />
          {data.summary.includes("WARNING: RESERVE INCLUDED") && (
            <p className="warning-text">
              <AlertTriangle size={16} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
              Reserve trigger detected in document.
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="fade-in">
      {renderAccuracyBadge()}
      {renderInsights()}

      <div className="glass-card">
        <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
          Incident Details
        </h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>Click any value below to highlight it in the original document.</p>
        <div className="grid-2">
          <div>
            <div className="field-label">Date/Time</div>
            <div className="field-value"><EditableField value={data.date_time} fieldName="date_time" docId="police_doc" needsReview={data.review_flags?.['date_time']} /></div>
          </div>
          <div>
            <div className="field-label">Location</div>
            <div className="field-value"><EditableField value={data.location} fieldName="location" docId="police_doc" needsReview={data.review_flags?.['location']} /></div>
          </div>
          <div>
            <div className="field-label">Weather</div>
            <div className="field-value"><EditableField value={data.weather} fieldName="weather" docId="police_doc" needsReview={data.review_flags?.['weather']} /></div>
          </div>
          <div>
            <div className="field-label">Accident Type</div>
            <div className="field-value"><EditableField value={data.accident_type} fieldName="accident_type" docId="police_doc" needsReview={data.review_flags?.['accident_type']} /></div>
          </div>
          <div>
            <div className="field-label">EMS Agency</div>
            <div className="field-value"><EditableField value={data.ems_agency} fieldName="ems_agency" docId="police_doc" needsReview={data.review_flags?.['ems_agency']} /></div>
          </div>
        </div>
      </div>

      <div className="glass-card">
        <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
          Agency & Investigation Details
        </h3>
        <div className="grid-2">
          <div>
            <div className="field-label">Responding Agency</div>
            <div className="field-value"><EditableField value={data.agency} fieldName="agency" docId="police_doc" needsReview={data.review_flags?.['agency']} /></div>
          </div>
          <div>
            <div className="field-label">Investigating Officer</div>
            <div className="field-value"><EditableField value={data.officer} fieldName="officer" docId="police_doc" needsReview={data.review_flags?.['officer']} /></div>
          </div>
          <div>
            <div className="field-label">Report Number</div>
            <div className="field-value"><EditableField value={data.report_number} fieldName="report_number" docId="police_doc" needsReview={data.review_flags?.['report_number']} /></div>
          </div>
        </div>
      </div>

      <div className="glass-card">
        <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
          Involved Vehicles & Parties
        </h3>
        
        <div style={{ marginBottom: '1.5rem' }}>
          <div className="field-label">Vehicles</div>
          {data.vehicles.map((v, idx) => (
            <div key={idx} style={{ background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '8px', marginBottom: '0.5rem' }}>
              <div className="grid-2" style={{ gap: '0.5rem' }}>
                <div><strong>VIN:</strong> <span className="clickable-field" onClick={() => onFieldClick('vin')}>{v.vin}</span> {v.vin !== "No VIN Found" && v.vin !== "Unknown" && <Badge />}</div>
                <div><strong>Plate:</strong> <span className="clickable-field" onClick={() => onFieldClick('plate')}>{v.plate}</span></div>
                <div><strong>Make/Model/Year:</strong> <span className="clickable-field" onClick={() => onFieldClick('make')}>{v.year} {v.make} {v.model}</span></div>
                <div><strong>Color:</strong> <span className="clickable-field" onClick={() => onFieldClick('color')}>{v.color}</span></div>
                <div><strong>Damages:</strong> <span className="clickable-field" onClick={() => onFieldClick('damages')}>{v.damages}</span></div>
                <div><strong>Towed/Company:</strong> <span className="clickable-field" onClick={() => onFieldClick('towed')}>{v.towed}</span> / <span className="clickable-field" onClick={() => onFieldClick('towing_company')}>{v.towing_company}</span></div>
                <div><strong>Owner:</strong> <span className="clickable-field" onClick={() => onFieldClick('owner_name')}>{v.owner_name}</span></div>
                <div><strong>Insurance (Policy):</strong> <span className="clickable-field" onClick={() => onFieldClick('insurance_company')}>{v.insurance_company}</span> (<span className="clickable-field" onClick={() => onFieldClick('policy_number')}>{v.policy_number}</span>)</div>
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <div className="field-label">Operators & Passengers</div>
          {data.parties && data.parties.length > 0 ? data.parties.map((p, idx) => (
            <div key={idx} style={{ background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '8px', marginBottom: '0.5rem' }}>
              <div className="grid-2" style={{ gap: '0.5rem' }}>
                <div><strong>Name:</strong> <span className="clickable-field" onClick={() => onFieldClick('name')}>{p.name}</span></div>
                <div><strong>DOB:</strong> <span className="clickable-field" onClick={() => onFieldClick('dob')}>{p.dob}</span></div>
                <div><strong>Address:</strong> <span className="clickable-field" onClick={() => onFieldClick('address')}>{p.address}</span></div>
                <div><strong>License:</strong> <span className="clickable-field" onClick={() => onFieldClick('license_number')}>{p.license_number}</span></div>
                <div><strong>Condition/Injuries:</strong> <span className="clickable-field" onClick={() => onFieldClick('condition')}>{p.condition}</span></div>
                <div><strong>Transported To:</strong> <span className="clickable-field" onClick={() => onFieldClick('transported_to')}>{p.transported_to}</span></div>
                <div><strong>Citations:</strong> <span className="clickable-field" onClick={() => onFieldClick('citations')}>{p.citations}</span></div>
              </div>
            </div>
          )) : <div style={{ fontSize: '0.9rem', fontStyle: 'italic', color: 'var(--text-muted)' }}>No parties identified in document.</div>}
        </div>

        <div>
          <div className="field-label">Witnesses</div>
          {data.witnesses && data.witnesses.length > 0 ? data.witnesses.map((w, idx) => (
            <div key={idx} style={{ background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '8px', marginBottom: '0.5rem' }}>
              <div className="grid-2" style={{ gap: '0.5rem' }}>
                <div><strong>Name:</strong> <span className="clickable-field" onClick={() => onFieldClick('name')}>{w.name}</span></div>
                <div><strong>DOB:</strong> <span className="clickable-field" onClick={() => onFieldClick('dob')}>{w.dob}</span></div>
                <div><strong>Address:</strong> <span className="clickable-field" onClick={() => onFieldClick('address')}>{w.address}</span></div>
              </div>
            </div>
          )) : <div style={{ fontSize: '0.9rem', fontStyle: 'italic', color: 'var(--text-muted)' }}>No witnesses identified in document.</div>}
        </div>
      </div>

      {data.state_codes && data.state_codes.length > 0 && (
        <div className="glass-card" style={{ marginBottom: '1rem' }}>
          <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
            State Code Lookup
          </h3>
          {data.state_codes.map((code, idx) => (
            <div key={idx} style={{ background: 'rgba(239, 68, 68, 0.1)', borderLeft: '4px solid var(--danger)', padding: '0.75rem', borderRadius: '4px', marginBottom: '0.5rem' }}>
              <strong>Code <span className="clickable-field" onClick={() => onFieldClick('code')}>{code.code}</span>:</strong> {code.description}
            </div>
          ))}
        </div>
      )}

      {data.dynamic_fields && Object.keys(data.dynamic_fields).length > 0 && (
        <div className="glass-card" style={{ marginBottom: '1rem' }}>
          <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
            Extracted Table Data & Custom Fields
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>Fields extracted automatically by the generic NLP engine.</p>
          <div className="grid-2">
            {Object.entries(data.dynamic_fields).map(([key, val], idx) => (
              <div key={idx}>
                <div className="field-label">{key}</div>
                <div className="field-value"><EditableField value={val} fieldName={key} docId="dynamic_doc" needsReview={data.review_flags?.[`dynamic_${key}`]} /></div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="glass-card" style={{ marginBottom: '1rem' }}>
        <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
          Adjuster Recommendations
        </h3>
        <textarea 
          style={{ width: '100%', minHeight: '80px', padding: '0.75rem', borderRadius: '4px', background: 'rgba(0,0,0,0.2)', color: 'white', border: '1px solid var(--border-color)' }}
          placeholder="Type final recommendations here..."
          value={recommendations}
          onChange={(e) => setRecommendations(e.target.value)}
        />
      </div>

      <div className="glass-card">
        <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FileTextIcon /> File Note Preview
        </h3>
        <p className="field-label" style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between' }}>
          <span>Ready for copy-pasting.</span>
          <span style={{ color: 'var(--text-muted)' }}><Info size={14} style={{ verticalAlign: 'text-bottom' }}/> ClaimCenter Integration Pending</span>
        </p>
        <textarea 
          className="file-note" 
          readOnly 
          value={recommendations.trim() ? `${data.summary} Recommendations: ${recommendations.trim()}` : data.summary} 
        />
      </div>

      <div className="glass-card" style={{ marginTop: '1rem', border: '1px solid var(--accent)' }}>
        <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent)' }}>
          <Plus size={18} /> Add Custom Extraction Field
        </h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Force the generic NLP engine to extract a specific field (e.g. "Ambulance Arrival Time") from this document.
        </p>
        <form onSubmit={addField} style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
          <input 
            type="text" 
            value={newField}
            onChange={(e) => setNewField(e.target.value)}
            placeholder="Type field name to extract..."
            style={{ flex: 1, padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'rgba(0,0,0,0.2)', color: 'white' }}
          />
          <button type="submit" className="btn-primary" disabled={!newField.trim()} style={{ padding: '0.5rem 1rem' }}>
            Add
          </button>
        </form>

        {customFields.length > 0 && (
          <div style={{ marginTop: '1rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {customFields.map((field, idx) => (
              <div key={idx} style={{ background: 'rgba(255,255,255,0.1)', padding: '0.25rem 0.5rem', borderRadius: '16px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                {field}
                <button onClick={() => deleteField(field)} style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', padding: 0 }}>
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
};

// Simple icon for File Note
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
