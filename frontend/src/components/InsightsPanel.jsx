import { ShieldCheck, AlertTriangle, Scale, Users, Car, Brain } from 'lucide-react';

export default function InsightsPanel({ data, type }) {
  if (!data) return null;

  const riskLevel = data.risk_level || 'low';
  const riskColors = {
    low: 'var(--success-bright)',
    medium: 'var(--warning)',
    high: 'var(--danger)',
  };
  const riskColor = riskColors[riskLevel];
  const score = data.accuracy_score || 0;

  const chips = [];
  if (data.reserve_warning) chips.push({
    label: 'Reserve language',
    cls: 'danger',
    icon: <AlertTriangle size={11} />
  });
  if (data.subrogation?.toLowerCase().includes('investig'))
    chips.push({
      label: 'Subrogation opportunity',
      cls: 'warning',
      icon: <Scale size={11} />
    });
  const partyCount = (data.operators||[]).length +
    (data.passengers||[]).length +
    (data.pedestrians||[]).length;
  if (partyCount > 0) chips.push({
    label: `${partyCount} parties`,
    cls: 'info',
    icon: <Users size={11} />
  });
  const vCount = (data.vehicles||[]).length;
  if (vCount > 0) chips.push({
    label: `${vCount} vehicles`,
    cls: 'info',
    icon: <Car size={11} />
  });
  if (data.form_id) chips.push({
    label: 'Form classified',
    cls: 'success',
    icon: <ShieldCheck size={11} />
  });

  const actions = [];
  if (data.reserve_warning) actions.push({
    text: `Set reserve — settlement estimated at ${data.settlement || 'TBD'}`,
    priority: 'urgent',
    priorityCls: 'danger',
  });
  if (data.subrogation?.toLowerCase().includes('investig'))
    actions.push({
      text: 'File subrogation preservation letter within 30 days',
      priority: '30 days',
      priorityCls: 'warning',
    });
  if (partyCount > 3) actions.push({
    text: `Review liability apportionment across ${partyCount} parties`,
    priority: 'review',
    priorityCls: 'warning',
  });
  if (!data.agency || data.agency === 'Unknown')
    actions.push({
      text: 'Request police supplement — agency field incomplete',
      priority: 'optional',
      priorityCls: 'info',
    });
  if (actions.length === 0) actions.push({
    text: 'Review extracted fields and submit to ClaimCenter',
    priority: 'review',
    priorityCls: 'info',
  });

  const chipStyle = (cls) => ({
    display: 'inline-flex', alignItems: 'center',
    gap: '5px', fontSize: '11px',
    padding: '4px 10px', borderRadius: '20px',
    border: `0.5px solid var(--${cls}-border, var(--border-color))`,
    background: `var(--${cls}-bg, rgba(147,197,253,0.08))`,
    color: cls === 'danger' ? 'var(--danger)'
      : cls === 'warning' ? 'var(--warning)'
      : cls === 'success' ? 'var(--success-bright)'
      : 'var(--accent)',
    margin: '2px',
  });

  return (
    <div style={{
      background: 'var(--surface-1)',
      borderBottom: '0.5px solid var(--nav-border)',
    }}>
      {/* Header */}
      <div style={{
        padding: '12px 16px',
        borderBottom: '0.5px solid var(--nav-border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div style={{
          display: 'flex', alignItems: 'center',
          gap: '6px', fontSize: '12px',
          fontWeight: '500', color: '#e2e8f0',
        }}>
          <Brain size={14} color="var(--accent)" />
          Claim intelligence
        </div>
        <div style={{
          display: 'flex',
          alignItems: 'center', gap: '12px',
        }}>
          <div style={{
            display: 'flex', alignItems: 'center',
            gap: '5px', fontSize: '11px',
            color: riskColor,
            fontFamily: 'var(--mono-font)',
          }}>
            <div style={{
              width: '6px', height: '6px',
              borderRadius: '50%',
              background: riskColor,
            }} />
            {riskLevel} risk
          </div>
          <div style={{
            fontSize: '20px', fontWeight: '500',
            color: score >= 90
              ? 'var(--success-bright)' : 'var(--warning)',
            fontFamily: 'var(--mono-font)',
          }}>
            {score.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Signal chips */}
      {chips.length > 0 && (
        <div style={{
          padding: '10px 16px',
          borderBottom: '0.5px solid var(--nav-border)',
        }}>
          <div style={{
            fontSize: '9px',
            color: 'var(--text-tertiary)',
            textTransform: 'uppercase',
            letterSpacing: '.1em',
            fontFamily: 'var(--mono-font)',
            marginBottom: '6px',
          }}>Signals detected</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
            {chips.map((c, i) => (
              <div key={i} style={chipStyle(c.cls)}>
                {c.icon}{c.label}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div style={{ padding: '10px 16px 14px' }}>
        <div style={{
          fontSize: '9px',
          color: 'var(--text-tertiary)',
          textTransform: 'uppercase',
          letterSpacing: '.1em',
          fontFamily: 'var(--mono-font)',
          marginBottom: '8px',
        }}>Next best actions</div>
        <div style={{
          display: 'flex',
          flexDirection: 'column', gap: '6px',
        }}>
          {actions.map((a, i) => (
            <div key={i} style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '10px', padding: '8px 10px',
              background: 'var(--surface-3,rgba(255,255,255,0.04))',
              borderRadius: '6px',
              border: '0.5px solid var(--nav-border)',
            }}>
              <div style={{
                width: '18px', height: '18px',
                borderRadius: '50%',
                background: a.priorityCls === 'danger'
                  ? 'rgba(239,68,68,0.15)'
                  : a.priorityCls === 'warning'
                  ? 'rgba(245,158,11,0.15)'
                  : 'rgba(147,197,253,0.15)',
                color: a.priorityCls === 'danger'
                  ? 'var(--danger)'
                  : a.priorityCls === 'warning'
                  ? 'var(--warning)' : 'var(--accent)',
                fontSize: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: 'var(--mono-font)',
                flexShrink: 0,
                marginTop: '1px',
              }}>{i + 1}</div>
              <div style={{ flex: 1, fontSize: '12px',
                color: '#e2e8f0', lineHeight: '1.4' }}>
                {a.text}
              </div>
              <div style={{
                fontSize: '9px',
                padding: '2px 6px',
                borderRadius: '10px',
                fontFamily: 'var(--mono-font)',
                background: a.priorityCls === 'danger'
                  ? 'rgba(239,68,68,0.15)'
                  : a.priorityCls === 'warning'
                  ? 'rgba(245,158,11,0.15)'
                  : 'rgba(147,197,253,0.15)',
                color: a.priorityCls === 'danger'
                  ? 'var(--danger)'
                  : a.priorityCls === 'warning'
                  ? 'var(--warning)' : 'var(--accent)',
                flexShrink: 0,
              }}>{a.priority}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
