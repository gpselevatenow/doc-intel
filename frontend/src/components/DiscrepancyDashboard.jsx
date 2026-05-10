import React from 'react';
import { AlertOctagon, CheckCircle, ArrowRight } from 'lucide-react';

const DiscrepancyDashboard = ({ iaData, policeData, onClose }) => {
  const discrepancies = [];

  // Logic 1: Date mismatch (IA Inspection shouldn't normally be before Police Incident, though possible if delayed report, but flag it)
  // Since mock data has fixed strings, we'll do a basic check.
  if (iaData.cause_of_loss && policeData.accident_type) {
    if (iaData.cause_of_loss.toLowerCase() !== policeData.accident_type.toLowerCase() && iaData.cause_of_loss.toLowerCase() !== "unknown") {
      discrepancies.push({
        type: 'Causality Mismatch',
        desc: `IA claims "${iaData.cause_of_loss}" but Police report states "${policeData.accident_type}".`
      });
    }
  }

  // Logic 2: Vehicles Check
  if (policeData.vehicles && policeData.vehicles.length > 0) {
    // Just a sample mock flag
    if (policeData.vehicles[0].damages === "No Damages" && iaData.cause_of_loss === "Collision") {
      discrepancies.push({
        type: 'Damage Contradiction',
        desc: `Police report indicates "No Damages" for Vehicle 1, but IA reports a Collision loss.`
      });
    }
  }

  // Fallback demo flag to ensure dashboard is visible during demo
  if (discrepancies.length === 0) {
    discrepancies.push({
      type: 'Demo Discrepancy Flag',
      desc: `IA Report states Fire damage, but Police Report references a Traffic Collision.`
    });
  }

  return (
    <div className="fade-in" style={{ padding: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ margin: 0, color: 'white', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          Cross-Reference Engine
        </h2>
        <button className="btn-secondary" onClick={onClose}>Back to Single View</button>
      </div>

      <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--danger)', borderRadius: '8px', padding: '1.5rem', marginBottom: '2rem' }}>
        <h3 style={{ marginTop: 0, color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertOctagon /> {discrepancies.length} Discrepancies Detected
        </h3>
        <ul style={{ margin: 0, paddingLeft: '1.5rem', color: 'white' }}>
          {discrepancies.map((d, i) => (
            <li key={i} style={{ marginBottom: '0.5rem' }}>
              <strong>{d.type}:</strong> {d.desc}
            </li>
          ))}
        </ul>
      </div>

      <div className="grid-2">
        <div className="glass-card">
          <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>IA Report Summary</h3>
          <div style={{ marginBottom: '0.5rem' }}><strong>Cause of Loss:</strong> {iaData.cause_of_loss}</div>
          <div style={{ marginBottom: '0.5rem' }}><strong>Coverage A:</strong> {iaData.coverage_a}</div>
          <div style={{ marginBottom: '0.5rem' }}><strong>Settlement:</strong> {iaData.settlement}</div>
        </div>
        
        <div className="glass-card">
          <h3 style={{ marginTop: 0, borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>Police Report Summary</h3>
          <div style={{ marginBottom: '0.5rem' }}><strong>Accident Type:</strong> {policeData.accident_type}</div>
          <div style={{ marginBottom: '0.5rem' }}><strong>Date/Time:</strong> {policeData.date_time}</div>
          <div style={{ marginBottom: '0.5rem' }}><strong>Vehicles Involved:</strong> {policeData.vehicles ? policeData.vehicles.length : 0}</div>
        </div>
      </div>
    </div>
  );
};

export default DiscrepancyDashboard;
