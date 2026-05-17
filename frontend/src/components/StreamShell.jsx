import { useState, useEffect, useRef } from 'react';
import InsightsPanel from './InsightsPanel';
import PersonCard from './PersonCard';
import VehicleCard from './VehicleCard';

const FIELD_LABELS = {
  date_time: 'Date / time',
  location: 'Location',
  weather: 'Weather conditions',
  road_surface: 'Road surface',
  light_condition: 'Light condition',
  accident_type: 'Accident type',
  agency: 'Agency',
  officer: 'Investigating officer',
  report_number: 'Report number',
  ems_agency: 'EMS agency',
  contributing_factors: 'Contributing factors',
  property_damage: 'Property damage',
  cause_of_loss: 'Cause of loss',
  settlement: 'Settlement estimate',
  subrogation: 'Subrogation status',
  coverage_a: 'Coverage A',
  coverage_b: 'Coverage B',
  coverage_c: 'Coverage C',
  coverage_d: 'Coverage D',
  inspection_date: 'Inspection date',
  inspection_firm: 'Inspection firm',
  officials: 'Officials',
  recommendations: 'Recommendations',
  payment_summary: 'Payment summary',
};

function AgentStep({ msg, status }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center',
      gap: '8px', padding: '5px 0',
      fontSize: '12px',
      color: status === 'done'
        ? 'var(--text-muted)'
        : '#e2e8f0',
    }}>
      <div style={{
        width: '16px', height: '16px',
        borderRadius: '50%', flexShrink: 0,
        display: 'flex', alignItems: 'center',
        justifyContent: 'center', fontSize: '10px',
        background: status === 'done'
          ? 'rgba(110,231,183,0.15)'
          : status === 'active'
          ? 'rgba(147,197,253,0.15)'
          : 'rgba(255,255,255,0.06)',
        color: status === 'done'
          ? 'var(--success-bright)'
          : status === 'active'
          ? 'var(--accent)'
          : 'var(--text-muted)',
      }}>
        {status === 'done' ? '✓'
          : status === 'active' ? '→' : '·'}
      </div>
      {msg}
    </div>
  );
}

function StreamField({ field_id, value,
  confidence, index, onFieldClick,
  onFieldHover, onFieldHoverEnd }) {
  const [displayed, setDisplayed] = useState('');
  const conf = Math.round((confidence || 0.85) * 100);
  const isHigh = conf >= 80;

  useEffect(() => {
    if (!value) return;
    const str = String(value);
    let i = 0;
    const delay = setTimeout(() => {
      const tick = setInterval(() => {
        i++;
        setDisplayed(str.slice(0, i));
        if (i >= str.length) clearInterval(tick);
      }, 22);
      return () => clearInterval(tick);
    }, index * 80);
    return () => clearTimeout(delay);
  }, [value, index]);

  return (
    <div
      onClick={() => onFieldClick?.(field_id)}
      onMouseEnter={() => onFieldHover?.(field_id)}
      onMouseLeave={() => onFieldHoverEnd?.()}
      style={{
        padding: '9px 12px',
        borderRadius: '7px',
        borderLeft: `2px solid ${isHigh
          ? 'var(--success-bright)'
          : 'var(--warning)'}`,
        background: isHigh
          ? 'rgba(16,185,129,0.06)'
          : 'rgba(245,158,11,0.06)',
        cursor: 'pointer',
        marginBottom: '5px',
        animation: `fieldLand 0.35s ease ${index * 80}ms both`,
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
          {FIELD_LABELS[field_id] || field_id}
        </div>
        <div style={{
          fontSize: '9px',
          color: isHigh
            ? 'var(--success-bright)'
            : 'var(--warning)',
          fontFamily: 'var(--mono-font)',
        }}>
          {isHigh ? 'AUTO' : 'REVIEW'} · {conf}%
        </div>
      </div>
      <div style={{
        fontSize: '13px', color: '#e2e8f0',
        fontFamily: 'var(--mono-font)',
        minHeight: '18px',
      }}>
        {displayed ||
          <span style={{ color: 'var(--text-tertiary)' }}>
            waiting...
          </span>}
      </div>
    </div>
  );
}

export default function StreamShell({
  file, docType, onFieldClick,
  onFieldHover, onFieldHoverEnd,
  onFieldHeartbeat, onFieldExtracted,
  onBboxEntry,
}) {
  const [steps, setSteps] = useState([]);
  const [fields, setFields] = useState([]);
  const [flags, setFlags] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [parties, setParties] = useState([]);
  const [done, setDone] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [syntheticData, setSyntheticData] = useState(null);
  const fieldIndex = useRef(0);

  // Keep refs so handleEvent closure always sees latest values
  const flagsRef = useRef([]);
  const vehiclesRef = useRef([]);
  const partiesRef = useRef([]);

  useEffect(() => {
    if (!file) return;
    setSteps([]);
    setFields([]);
    setFlags([]);
    setVehicles([]);
    setParties([]);
    setDone(false);
    setSyntheticData(null);
    fieldIndex.current = 0;
    flagsRef.current = [];
    vehiclesRef.current = [];
    partiesRef.current = [];
    setStreaming(true);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('doc_type', docType || 'police_report');

    fetch('http://localhost:8004/api/extract/stream',
      { method: 'POST', body: formData })
      .then(res => {
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        function read() {
          reader.read().then(({ done: d, value }) => {
            if (d) { setStreaming(false); return; }
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop() || '';
            lines.forEach(line => {
              if (!line.startsWith('data: ')) return;
              try {
                const event = JSON.parse(line.slice(6));
                handleEvent(event);
              } catch {}
            });
            read();
          });
        }
        read();
      })
      .catch(() => setStreaming(false));
  }, [file]);

  function handleEvent(event) {
    switch (event.type) {
      case 'step':
      case 'classified':
        setSteps(prev => [...prev, { msg: event.msg, status: 'done' }]);
        break;
      case 'field':
        console.log('field event firing heartbeat:', event.field_id);
        onFieldHeartbeat?.(event.field_id);
        setTimeout(() => {
          onFieldExtracted?.(event.field_id);
          onFieldHeartbeat?.(null);
        }, 600);
        setFields(prev => [...prev, { ...event, index: fieldIndex.current++ }]);
        break;
      case 'flag':
        flagsRef.current = [...flagsRef.current, event.flag];
        setFlags(flagsRef.current);
        break;
      case 'vehicles':
        vehiclesRef.current = event.data || [];
        setVehicles(vehiclesRef.current);
        break;
      case 'parties':
        partiesRef.current = event.data || [];
        setParties(partiesRef.current);
        break;
      case 'bbox':
        onBboxEntry?.(event.field_id, {
          bbox: event.bbox,
          page: event.page,
          value: event.value,
        });
        break;
      case 'done':
        setDone(true);
        setStreaming(false);
        setSyntheticData({
          risk_level: event.risk_level,
          accuracy_score: 97,
          reserve_warning: flagsRef.current.includes('reserve'),
          vehicles: vehiclesRef.current,
          operators: partiesRef.current.filter(p => p.role?.toLowerCase() === 'operator'),
          passengers: partiesRef.current.filter(p => p.role?.toLowerCase() === 'passenger'),
          pedestrians: partiesRef.current.filter(p => ['pedestrian', 'bicyclist'].includes(p.role?.toLowerCase())),
        });
        break;
    }
  }

  if (!file) return (
    <div style={{
      display: 'flex', alignItems: 'center',
      justifyContent: 'center', height: '100%',
      color: 'var(--text-tertiary)', fontSize: '13px',
    }}>
      Select a document to begin streaming
    </div>
  );

  return (
    <div style={{
      height: '100%', overflowY: 'auto',
      display: 'flex', flexDirection: 'column',
    }}>
      {done && syntheticData && (
        <InsightsPanel data={syntheticData} type={docType} />
      )}

      {steps.length > 0 && (
        <div style={{
          padding: '12px 16px',
          borderBottom: '0.5px solid var(--nav-border)',
          background: streaming
            ? 'rgba(147,197,253,0.03)'
            : 'transparent',
        }}>
          {steps.map((s, i) => (
            <AgentStep key={i} msg={s.msg} status={s.status} />
          ))}
          {streaming
            ? <AgentStep msg="Extracting..." status="active" />
            : done
            ? <AgentStep msg="Extraction complete ✓" status="done" />
            : null
          }
        </div>
      )}

      {flags.includes('reserve') && (
        <div style={{
          margin: '12px 16px 0',
          padding: '10px 12px',
          background: 'rgba(239,68,68,0.08)',
          border: '0.5px solid rgba(239,68,68,0.3)',
          borderLeft: '3px solid var(--danger)',
          borderRadius: '6px',
          fontSize: '11px',
          color: 'var(--danger)',
          fontFamily: 'var(--mono-font)',
        }}>
          ⚠ Reserve language detected
        </div>
      )}

      {fields.length > 0 && (
        <div style={{ padding: '14px 16px' }}>
          <div style={{
            fontSize: '9px',
            color: 'var(--text-tertiary)',
            textTransform: 'uppercase',
            letterSpacing: '.1em',
            fontFamily: 'var(--mono-font)',
            marginBottom: '10px',
          }}>
            Extracted fields ({fields.length}
            {streaming ? ' · streaming...' : ' · complete'})
          </div>
          {fields.map((f) => (
            <StreamField
              key={f.field_id}
              {...f}
              onFieldClick={onFieldClick}
              onFieldHover={onFieldHover}
              onFieldHoverEnd={onFieldHoverEnd}
            />
          ))}
        </div>
      )}

      {vehicles.length > 0 && (
        <div style={{ padding: '0 16px 14px' }}>
          <div style={{
            fontSize: '9px',
            color: 'var(--text-tertiary)',
            textTransform: 'uppercase',
            letterSpacing: '.1em',
            fontFamily: 'var(--mono-font)',
            marginBottom: '10px',
            paddingTop: '14px',
            borderTop: '0.5px solid var(--nav-border)',
          }}>
            Vehicles ({vehicles.length})
          </div>
          {vehicles.map((v, i) => (
            <VehicleCard key={i} vehicle={v} index={i} />
          ))}
        </div>
      )}

      {parties.length > 0 && (
        <div style={{ padding: '0 16px 14px' }}>
          <div style={{
            fontSize: '9px',
            color: 'var(--text-tertiary)',
            textTransform: 'uppercase',
            letterSpacing: '.1em',
            fontFamily: 'var(--mono-font)',
            marginBottom: '10px',
            paddingTop: '14px',
            borderTop: '0.5px solid var(--nav-border)',
          }}>
            Parties ({parties.length})
          </div>
          {parties.map((p, i) => (
            <PersonCard key={i} party={p} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}
