import React from 'react';

export const bboxPlugin = (props) => {
  const { bboxMap, selectedFieldRef, hoveredFieldRef } = props;

  return {
    renderPageLayer: (renderPageProps) => {
      console.log('render page, hoveredField:', hoveredFieldRef?.current, 'bboxMap keys:', Object.keys(bboxMap || {}).slice(0, 3));
      const { pageIndex, width, height } = renderPageProps;
      const PAGE_HEIGHT_PT = height / renderPageProps.scale;

      const boxes = Object.entries(bboxMap || {})
        .filter(([_, info]) => info.page === pageIndex + 1)
        .map(([fieldId, info]) => {
          const [l, t, r, b] = info.bbox;
          const scaleX = width / 612;
          const flippedT = PAGE_HEIGHT_PT - t;
          const flippedB = PAGE_HEIGHT_PT - b;
          const left = l * scaleX;
          const top = Math.min(flippedT, flippedB) * scaleX;
          const w = (r - l) * scaleX;
          const h = Math.abs(flippedT - flippedB) * scaleX;
          const isSelected = selectedFieldRef?.current === fieldId;
          const isHovered = hoveredFieldRef?.current === fieldId;
          return { fieldId, left, top, w, h, isSelected, isHovered };
        });

      return (
        <div style={{
          position: 'absolute', top: 0, left: 0,
          width: '100%', height: '100%',
          pointerEvents: 'none', overflow: 'visible',
        }}>
          {boxes.map(({ fieldId, left, top, w, h, isSelected, isHovered }) => (
            <div key={fieldId}>

              {/* Highlight box */}
              <div style={{
                position: 'absolute',
                left, top, width: w, height: h,
                border: isSelected
                  ? '2px solid #ef4444'
                  : isHovered
                  ? '1.5px solid rgba(139,92,246,0.8)'
                  : '1px solid rgba(147,197,253,0.4)',
                background: isSelected
                  ? 'rgba(239,68,68,0.12)'
                  : isHovered
                  ? 'rgba(139,92,246,0.15)'
                  : 'rgba(147,197,253,0.06)',
                borderRadius: '2px',
                transition: 'all 0.2s ease',
                animation: isSelected ? 'selectedPulse 0.8s ease-out' : 'none',
              }} />

              {/* Semantic Lens card — only on hover */}
              {isHovered && bboxMap[fieldId] && (
                <div style={{
                  position: 'absolute',
                  left: left + w + 12,
                  top: Math.max(0, top - 16),
                  width: '240px',
                  background: 'rgba(8,12,28,0.95)',
                  backdropFilter: 'blur(16px)',
                  WebkitBackdropFilter: 'blur(16px)',
                  border: '1px solid rgba(139,92,246,0.6)',
                  borderRadius: '12px',
                  padding: '14px 16px',
                  zIndex: 100,
                  boxShadow: `
                    0 0 0 1px rgba(139,92,246,0.2),
                    0 0 20px rgba(139,92,246,0.25),
                    0 0 40px rgba(139,92,246,0.1),
                    0 8px 32px rgba(0,0,0,0.6)
                  `,
                  animation: 'lensAppear 0.18s cubic-bezier(0.34,1.56,0.64,1)',
                  fontFamily: 'JetBrains Mono, Fira Code, monospace',
                  fontSize: '11px',
                  lineHeight: '1.7',
                }}>
                  {/* Glow accent line at top */}
                  <div style={{
                    position: 'absolute',
                    top: 0, left: '20%', right: '20%',
                    height: '1px',
                    background: 'linear-gradient(90deg, transparent, rgba(139,92,246,0.8), transparent)',
                    borderRadius: '1px',
                  }} />

                  {/* JSON opening brace */}
                  <div style={{ color: '#e2e8f0', marginBottom: '4px' }}>{'{'}</div>

                  {/* Field entries */}
                  <div style={{ paddingLeft: '12px' }}>
                    <div>
                      <span style={{ color: '#93c5fd' }}>"field"</span>
                      <span style={{ color: '#e2e8f0' }}>: </span>
                      <span style={{ color: '#a78bfa' }}>"{fieldId.replace(/_/g, ' ')}"</span>
                      <span style={{ color: '#e2e8f0' }}>,</span>
                    </div>
                    <div>
                      <span style={{ color: '#93c5fd' }}>"value"</span>
                      <span style={{ color: '#e2e8f0' }}>: </span>
                      <span style={{ color: '#6ee7b7' }}>"{(bboxMap[fieldId]?.value || '—').slice(0, 40)}"</span>
                      <span style={{ color: '#e2e8f0' }}>,</span>
                    </div>
                    <div>
                      <span style={{ color: '#93c5fd' }}>"status"</span>
                      <span style={{ color: '#e2e8f0' }}>: </span>
                      <span style={{ color: '#6ee7b7' }}>"Extracted"</span>
                      <span style={{ color: '#e2e8f0' }}>,</span>
                    </div>
                    <div>
                      <span style={{ color: '#93c5fd' }}>"source"</span>
                      <span style={{ color: '#e2e8f0' }}>: </span>
                      <span style={{ color: '#fbbf24' }}>"Page {bboxMap[fieldId]?.page}"</span>
                    </div>
                  </div>

                  {/* JSON closing brace */}
                  <div style={{ color: '#e2e8f0', marginTop: '4px' }}>{'}'}</div>

                  {/* Connector dot */}
                  <div style={{
                    position: 'absolute',
                    left: '-5px',
                    top: '20px',
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: 'rgba(139,92,246,0.9)',
                    boxShadow: '0 0 8px rgba(139,92,246,0.8)',
                  }} />

                  {/* Connector line */}
                  <div style={{
                    position: 'absolute',
                    left: '-12px',
                    top: '23px',
                    width: '8px',
                    height: '1px',
                    background: 'rgba(139,92,246,0.6)',
                  }} />
                </div>
              )}
            </div>
          ))}
        </div>
      );
    }
  };
};
