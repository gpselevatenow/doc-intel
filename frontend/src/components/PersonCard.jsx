import { useState } from 'react';
import { Calendar, CreditCard, MapPin, Phone } from 'lucide-react';

function getInitials(name) {
  if (!name) return '?';
  return name.split(' ').map(w => w[0]).filter(Boolean).join('').slice(0, 2).toUpperCase();
}

function roleMeta(role) {
  const r = (role || '').toLowerCase();
  if (r === 'operator') return { label: 'Driver', bg: 'rgba(147,197,253,0.15)', color: 'var(--accent)' };
  if (r === 'passenger') return { label: 'Passenger', bg: 'rgba(167,243,208,0.15)', color: 'var(--success-bright)' };
  return { label: 'Pedestrian', bg: 'rgba(253,230,138,0.15)', color: 'var(--warning)' };
}

export default function PersonCard({ party, index }) {
  const [validated, setValidated] = useState(false);
  const { label, bg, color } = roleMeta(party.role);
  const injured = party.injuries
    && party.injuries.toLowerCase() !== 'none'
    && party.injuries.trim() !== '';

  const infoRows = [
    party.dob          && { icon: <Calendar size={11} />,   label: 'DOB',     value: party.dob },
    party.license_number && { icon: <CreditCard size={11} />, label: 'License', value: party.license_number },
    party.address      && { icon: <MapPin size={11} />,     label: 'Address',  value: party.address },
    party.phone        && { icon: <Phone size={11} />,      label: 'Phone',    value: party.phone },
  ].filter(Boolean);

  return (
    <div style={{
      background: 'rgba(15,23,42,0.6)',
      border: '0.5px solid var(--nav-border)',
      borderRadius: '8px',
      padding: '12px',
      marginBottom: '8px',
      animation: `fieldLand 0.35s ease ${index * 60}ms both`,
    }}>
      <div style={{
        display: 'flex', alignItems: 'flex-start',
        gap: '10px', marginBottom: infoRows.length ? '10px' : '0',
      }}>
        <div style={{
          width: '36px', height: '36px', borderRadius: '50%',
          background: 'rgba(147,197,253,0.12)',
          border: '1px solid rgba(147,197,253,0.22)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '12px', fontWeight: 600,
          color: 'var(--accent)', flexShrink: 0,
          fontFamily: 'var(--mono-font)',
        }}>
          {getInitials(party.name)}
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontSize: '13px', color: '#e2e8f0',
            fontWeight: 500, marginBottom: '5px',
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          }}>
            {party.name || 'Unknown'}
          </div>
          <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
            <span style={{
              fontSize: '9px', padding: '2px 6px', borderRadius: '3px',
              background: bg, color,
              fontFamily: 'var(--mono-font)',
              textTransform: 'uppercase', letterSpacing: '.06em',
            }}>
              {label}
            </span>
            <span style={{
              fontSize: '9px', padding: '2px 6px', borderRadius: '3px',
              background: injured ? 'rgba(239,68,68,0.12)' : 'rgba(110,231,183,0.10)',
              color: injured ? 'var(--danger)' : 'var(--success-bright)',
              fontFamily: 'var(--mono-font)',
              textTransform: 'uppercase', letterSpacing: '.06em',
            }}>
              {injured ? 'Injured' : 'Not injured'}
            </span>
          </div>
        </div>

        <button
          onClick={() => setValidated(v => !v)}
          style={{
            fontSize: '9px', padding: '3px 8px', borderRadius: '4px',
            border: `1px solid ${validated ? 'rgba(110,231,183,0.4)' : 'rgba(255,255,255,0.08)'}`,
            background: validated ? 'rgba(110,231,183,0.10)' : 'rgba(255,255,255,0.04)',
            color: validated ? 'var(--success-bright)' : 'var(--text-muted)',
            cursor: 'pointer', fontFamily: 'var(--mono-font)',
            textTransform: 'uppercase', letterSpacing: '.06em',
            whiteSpace: 'nowrap', flexShrink: 0,
          }}
        >
          {validated ? '✓ Validated' : 'Pending'}
        </button>
      </div>

      {infoRows.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '5px' }}>
          {infoRows.map(({ icon, label: lbl, value }, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'flex-start', gap: '5px',
              padding: '5px 7px',
              background: 'rgba(255,255,255,0.03)',
              borderRadius: '5px',
            }}>
              <span style={{ color: 'var(--text-tertiary)', marginTop: '1px', flexShrink: 0 }}>
                {icon}
              </span>
              <div style={{ minWidth: 0 }}>
                <div style={{
                  fontSize: '8px', color: 'var(--text-tertiary)',
                  fontFamily: 'var(--mono-font)',
                  textTransform: 'uppercase', letterSpacing: '.06em',
                  marginBottom: '1px',
                }}>
                  {lbl}
                </div>
                <div style={{
                  fontSize: '11px', color: '#e2e8f0',
                  fontFamily: 'var(--mono-font)', wordBreak: 'break-word',
                }}>
                  {value}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
