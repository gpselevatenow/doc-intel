import React from 'react';

export const bboxPlugin = (props) => {
    const { bboxMap, selectedField } = props;

    return {
        renderPageLayer: (renderPageProps) => {
            // Find all boxes that belong to this page
            // bboxMap is like { "location": { bbox: [l,t,r,b], page: 1 }, "date_time": ... }
            const currentBoxes = [];
            if (bboxMap) {
                Object.entries(bboxMap).forEach(([fieldId, info]) => {
                    if (info.page === renderPageProps.pageIndex + 1) {
                        currentBoxes.push({ fieldId, ...info });
                    }
                });
            }

            if (currentBoxes.length === 0) return <React.Fragment />;

            return (
                <>
                    {currentBoxes.map((box, idx) => {
                        const [l, t, r, b] = box.bbox;
                        // docling returns bboxes in absolute PDF points.
                        // renderPageProps gives us the scaled width/height.
                        // We use percentages to map the points onto the scaled container.
                        // docling origin is BOTTOM-LEFT. CSS top is TOP-LEFT.
                        const pageWidthPt = renderPageProps.width / renderPageProps.scale;
                        const pageHeightPt = renderPageProps.height / renderPageProps.scale;

                        const left = (l / pageWidthPt) * 100;
                        const top = ((pageHeightPt - t) / pageHeightPt) * 100;
                        const width = ((r - l) / pageWidthPt) * 100;
                        const height = ((t - b) / pageHeightPt) * 100;

                        const isSelected = selectedField === box.fieldId;

                        return (
                            <div
                                key={idx}
                                title={box.fieldId}
                                style={{
                                    position: 'absolute',
                                    left: `${left}%`,
                                    top: `${top}%`,
                                    width: `${width}%`,
                                    height: `${height}%`,
                                    border: isSelected ? '2px solid red' : '1px solid var(--accent)',
                                    backgroundColor: isSelected ? 'rgba(255, 0, 0, 0.25)' : 'rgba(0, 204, 255, 0.1)',
                                    zIndex: isSelected ? 20 : 10,
                                    pointerEvents: 'none',
                                    borderRadius: '2px',
                                    transition: 'all 0.2s ease-in-out',
                                    boxShadow: isSelected ? '0 0 8px rgba(255,0,0,0.5)' : 'none'
                                }}
                            />
                        );
                    })}
                </>
            );
        }
    };
};
