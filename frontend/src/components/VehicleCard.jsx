import { Car } from 'lucide-react';

export default function VehicleCard({ vehicle, index }) {
  const hasVin = Boolean(vehicle.vin);
  const vinDisplay = vehicle.vin
    ? (vehicle.vin.length > 10 ? vehicle.vin.slice(0, 10) + '...' : vehicle.vin)
    : '—';

  const ymm = [vehicle.year, vehicle.make, vehicle.model]
    .filter(Boolean).join(' ') || 'Unknown vehicle';

  const gridRows = [
    { label: 'Plate',  value: vehicle.plate  || '—' },
    { label: 'VIN',   value: vinDisplay },
    { label: 'Color',  value: vehicle.color  || '—' },
    { label: 'Damage', value: vehicle.damage || '—' },
  ];

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
        display: 'flex', alignItems: 'center',
        gap: '12px', marginBottom: '10px',
      }}>
        <div style={{
          width: '72px', height: '50px',
          background: 'rgba(147,197,253,0.06)',
          border: '0.5px solid rgba(147,197,253,0.14)',
          borderRadius: '6px',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0, color: 'rgba(147,197,253,0.35)',
          position: 'relative',
        }}>
          <Car size={28} />
          <span style={{
            position: 'absolute', top: '4px', right: '5px',
            fontSize: '8px', fontFamily: 'var(--mono-font)',
            color: 'var(--text-tertiary)',
          }}>
            V{index + 1}
          </span>
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontSize: '13px', color: '#e2e8f0',
            fontWeight: 500, marginBottom: '5px',
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          }}>
            {ymm}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <div style={{
              width: '7px', height: '7px', borderRadius: '50%', flexShrink: 0,
              background: hasVin ? 'var(--success-bright)' : 'rgba(255,255,255,0.15)',
            }} />
            <span style={{
              fontSize: '9px', color: 'var(--text-muted)',
              fontFamily: 'var(--mono-font)',
            }}>
              {hasVin ? 'VIN confirmed' : 'No VIN'}
            </span>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '5px' }}>
        {gridRows.map(({ label, value }, i) => (
          <div key={i} style={{
            padding: '5px 7px',
            background: 'rgba(255,255,255,0.03)',
            borderRadius: '5px',
          }}>
            <div style={{
              fontSize: '8px', color: 'var(--text-tertiary)',
              fontFamily: 'var(--mono-font)',
              textTransform: 'uppercase', letterSpacing: '.06em',
              marginBottom: '2px',
            }}>
              {label}
            </div>
            <div style={{
              fontSize: '11px', color: '#e2e8f0',
              fontFamily: 'var(--mono-font)', wordBreak: 'break-word',
            }}>
              {value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
