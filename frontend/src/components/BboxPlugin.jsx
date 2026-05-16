import React from 'react';

export const bboxPlugin = (props) => {
  const { bboxMap, selectedField, hoveredField } = props;

  return {
    renderPageLayer: (renderPageProps) => {
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
          const isSelected = fieldId === selectedField;
          const isHovered = fieldId === hoveredField;
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
                  ? '2px solid #93c5fd'
                  : '1px solid rgba(147,197,253,0.4)',
                background: isSelected
                  ? 'rgba(239,68,68,0.12)'
                  : isHovered
                  ? 'rgba(147,197,253,0.15)'
                  : 'rgba(147,197,253,0.06)',
                borderRadius: '2px',
                transition: 'all 0.2s ease',
                animation: isSelected ? 'selectedPulse 0.8s ease-out' : 'none',
              }} />

              {/* Semantic Lens card — only on hover */}
              {isHovered && (
                <div style={{
                  position: 'absolute',
                  left: left + w + 8,
                  top: Math.max(0, top - 8),
                  width: '200px',
                  background: 'rgba(6,14,29,0.92)',
                  backdropFilter: 'blur(12px)',
                  WebkitBackdropFilter: 'blur(12px)',
                  border: '0.5px solid rgba(147,197,253,0.3)',
                  borderRadius: '10px',
                  padding: '12px 14px',
                  zIndex: 100,
                  boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
                  animation: 'lensAppear 0.15s ease-out',
                }}>
                  {/* Field ID label */}
                  <div style={{
                    fontSize: '9px',
                    color: '#93c5fd',
                    fontFamily: 'JetBrains Mono, monospace',
                    textTransform: 'uppercase',
                    letterSpacing: '.1em',
                    marginBottom: '6px',
                  }}>
                    {fieldId.replace(/_/g, ' ')}
                  </div>

                  {/* Extracted value */}
                  <div style={{
                    fontSize: '12px',
                    color: '#f1f5f9',
                    fontFamily: 'JetBrains Mono, monospace',
                    lineHeight: '1.4',
                    marginBottom: '8px',
                    wordBreak: 'break-word',
                  }}>
                    {bboxMap[fieldId]?.value || '—'}
                  </div>

                  {/* Connector line */}
                  <div style={{
                    position: 'absolute',
                    left: '-8px',
                    top: '16px',
                    width: '8px',
                    height: '1px',
                    background: 'rgba(147,197,253,0.5)',
                  }} />

                  {/* Source tag */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <div style={{
                      width: '6px', height: '6px',
                      borderRadius: '50%',
                      background: '#10b981',
                    }} />
                    <span style={{
                      fontSize: '10px',
                      color: '#475569',
                      fontFamily: 'JetBrains Mono, monospace',
                    }}>extracted · auto-accepted</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      );
    }
  };
};
