import React from 'react';

export const bboxPlugin = (props) => {
  const {
    bboxMap,
    selectedFieldRef,
    hoveredFieldRef,
    heartbeatFieldRef,
    extractedFieldsRef,
  } = props;

  return {
    renderPageLayer: (renderPageProps) => {
      const { pageIndex, width, height } = renderPageProps;
      const PAGE_HEIGHT_PT = height / renderPageProps.scale;

      const entries = Object.entries(bboxMap || {}).filter(
        ([_, info]) => info.page === pageIndex + 1
      );

      if (entries.length === 0) return <React.Fragment />;

      return (
        <div style={{
          position: 'absolute', top: 0, left: 0,
          width: '100%', height: '100%',
          pointerEvents: 'none', overflow: 'visible',
        }}>
          {entries.map(([fieldId, info]) => {
            const [l, t, r, b] = info.bbox;
            const scaleX = width / 612;
            const ph = PAGE_HEIGHT_PT;
            const flippedT = ph - t;
            const flippedB = ph - b;
            const left = l * scaleX;
            const top = Math.min(flippedT, flippedB) * scaleX;
            const w = (r - l) * scaleX;
            const h = Math.abs(flippedT - flippedB) * scaleX;

            const isSelected  = selectedFieldRef?.current  === fieldId;
            const isHovered   = hoveredFieldRef?.current   === fieldId;
            const isHeartbeat = heartbeatFieldRef?.current === fieldId;
            const isExtracted = extractedFieldsRef?.current?.has(fieldId);

            let border, bg, animation;

            if (isSelected) {
              border    = '2px solid #ef4444';
              bg        = 'rgba(239,68,68,0.12)';
              animation = 'selectedPulse 0.8s ease-out';
            } else if (isHeartbeat) {
              border    = '2px solid rgba(147,197,253,0.9)';
              bg        = 'rgba(147,197,253,0.2)';
              animation = 'heartbeatPulse 0.8s ease-in-out infinite';
            } else if (isExtracted) {
              border    = '1.5px solid rgba(16,185,129,0.6)';
              bg        = 'rgba(16,185,129,0.08)';
              animation = 'none';
            } else if (isHovered) {
              border    = '2px solid rgba(139,92,246,0.8)';
              bg        = 'rgba(139,92,246,0.15)';
              animation = 'none';
            } else {
              return null;
            }

            return (
              <div key={fieldId}>
                <div style={{
                  position: 'absolute',
                  left, top, width: w, height: h,
                  border, background: bg,
                  borderRadius: '2px',
                  transition: 'all 0.3s ease',
                  animation,
                }} />
                {isExtracted && !isSelected && (
                  <div style={{
                    position: 'absolute',
                    left: left + w + 4,
                    top: top + h / 2 - 8,
                    background: 'rgba(16,185,129,0.9)',
                    color: 'white',
                    fontSize: '9px',
                    padding: '1px 5px',
                    borderRadius: '3px',
                    fontFamily: 'var(--mono-font)',
                    whiteSpace: 'nowrap',
                    pointerEvents: 'none',
                  }}>
                    {(info.value || '').slice(0, 20)}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      );
    },
  };
};
