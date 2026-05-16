import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

function buildNodes(data) {
  const nodes = [];
  const links = [];

  // Central incident node
  nodes.push({
    id: 'incident',
    label: data.accident_type
      ? data.accident_type.slice(0, 20)
      : 'Incident',
    type: 'incident',
    mass: 8,
    color: '#ef4444',
    detail: data.accident_type || '',
  });

  // Risk flags
  if (data.reserve_warning) {
    nodes.push({
      id: 'reserve',
      label: 'Reserve',
      type: 'flag',
      mass: 6,
      color: '#ef4444',
      detail: 'Reserve language detected',
    });
    links.push({
      source: 'incident',
      target: 'reserve',
      strength: 0.8,
    });
  }

  if (data.subrogation?.toLowerCase().includes('investig')) {
    nodes.push({
      id: 'subrogation',
      label: 'Subrogation',
      type: 'flag',
      mass: 5,
      color: '#f59e0b',
      detail: data.subrogation,
    });
    links.push({
      source: 'incident',
      target: 'subrogation',
      strength: 0.6,
    });
  }

  // Weather node
  if (data.weather && data.weather !== 'Unknown') {
    nodes.push({
      id: 'weather',
      label: data.weather.slice(0, 15),
      type: 'condition',
      mass: 3,
      color: '#93c5fd',
      detail: data.weather,
    });
    links.push({
      source: 'incident',
      target: 'weather',
      strength: 0.3,
    });
  }

  // Vehicle nodes
  const vehicles = data.vehicles || [];
  vehicles.slice(0, 5).forEach((v, i) => {
    const vid = `vehicle_${i}`;
    nodes.push({
      id: vid,
      label: `V${i + 1} ${v.make || ''}`.trim(),
      type: 'vehicle',
      mass: 4,
      color: '#378ADD',
      detail: [v.year, v.make, v.model, v.plate].filter(Boolean).join(' · '),
    });
    links.push({
      source: 'incident',
      target: vid,
      strength: 0.5,
    });

    // Link operators to vehicles
    const operators = data.operators || [];
    operators.slice(0, 4).forEach((op, j) => {
      const opid = `operator_${j}`;
      if (i === j) {
        links.push({
          source: vid,
          target: opid,
          strength: 0.7,
        });
      }
    });
  });

  // Operator nodes
  const operators = data.operators || [];
  operators.slice(0, 4).forEach((op, i) => {
    const hasInjury =
      op.injuries &&
      op.injuries !== 'No apparent injury' &&
      op.injuries !== 'Unknown';
    nodes.push({
      id: `operator_${i}`,
      label: (op.name || 'Operator').split(' ').slice(0, 2).join(' '),
      type: 'person',
      mass: hasInjury ? 5 : 3,
      color: hasInjury ? '#f87171' : '#a78bfa',
      detail: [op.name, op.role, op.injuries].filter(Boolean).join(' · '),
    });
    links.push({
      source: 'incident',
      target: `operator_${i}`,
      strength: 0.4,
    });
  });

  // Pedestrian nodes
  const peds = data.pedestrians || [];
  peds.slice(0, 3).forEach((p, i) => {
    nodes.push({
      id: `ped_${i}`,
      label: (p.name || 'Pedestrian').split(' ')[0],
      type: 'pedestrian',
      mass: 4,
      color: '#f87171',
      detail: p.name || 'Pedestrian',
    });
    links.push({
      source: 'incident',
      target: `ped_${i}`,
      strength: 0.5,
    });
  });

  return { nodes, links };
}

export default function GravityModel({ data }) {
  const svgRef = useRef(null);
  const [selected, setSelected] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!data || !svgRef.current) return;
    const { nodes, links } = buildNodes(data);
    if (nodes.length < 2) return;

    const W = svgRef.current.clientWidth || 600;
    const H = 420;

    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current).attr('width', W).attr('height', H);

    // Dark background
    svg.append('rect')
      .attr('width', W)
      .attr('height', H)
      .attr('fill', '#060b16')
      .attr('rx', 12);

    const sim = d3
      .forceSimulation(nodes)
      .force(
        'link',
        d3
          .forceLink(links)
          .id((d) => d.id)
          .strength((d) => d.strength || 0.5)
          .distance(80)
      )
      .force(
        'charge',
        d3.forceManyBody().strength((d) => -d.mass * 20)
      )
      .force('center', d3.forceCenter(W / 2, H / 2))
      .force(
        'collision',
        d3.forceCollide().radius((d) => d.mass * 4 + 10)
      );

    // Links
    const link = svg
      .append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', 'rgba(255,255,255,0.1)')
      .attr('stroke-width', 1);

    // Node groups
    const node = svg
      .append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .style('cursor', 'pointer')
      .call(
        d3
          .drag()
          .on('start', (event, d) => {
            if (!event.active) sim.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active) sim.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      )
      .on('click', (event, d) => {
        setSelected(d);
        event.stopPropagation();
      });

    // Circles
    node
      .append('circle')
      .attr('r', (d) => d.mass * 3 + 6)
      .attr('fill', (d) => d.color + '22')
      .attr('stroke', (d) => d.color)
      .attr('stroke-width', 1.5);

    // Pulse ring for high-risk nodes
    node
      .filter((d) => d.mass >= 5)
      .append('circle')
      .attr('r', (d) => d.mass * 3 + 12)
      .attr('fill', 'none')
      .attr('stroke', (d) => d.color)
      .attr('stroke-width', 0.5)
      .attr('opacity', 0.3);

    // Labels
    node
      .append('text')
      .text((d) => d.label)
      .attr('text-anchor', 'middle')
      .attr('dy', (d) => d.mass * 3 + 20)
      .attr('fill', '#94a3b8')
      .attr('font-size', '10px')
      .attr('font-family', 'JetBrains Mono, monospace');

    // Type icons in circle
    node
      .append('text')
      .text((d) =>
        d.type === 'incident'
          ? '⚡'
          : d.type === 'vehicle'
          ? '🚗'
          : d.type === 'person'
          ? '👤'
          : d.type === 'flag'
          ? '⚠'
          : d.type === 'pedestrian'
          ? '🚶'
          : '●'
      )
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('font-size', (d) => (d.mass >= 6 ? '16px' : '12px'));

    sim.on('tick', () => {
      link
        .attr('x1', (d) => d.source.x)
        .attr('y1', (d) => d.source.y)
        .attr('x2', (d) => d.target.x)
        .attr('y2', (d) => d.target.y);
      node.attr('transform', (d) => `translate(${d.x},${d.y})`);
    });

    // Click background to deselect
    svg.on('click', () => setSelected(null));

    setTimeout(() => setReady(true), 500);

    return () => sim.stop();
  }, [data]);

  if (!data) return null;

  return (
    <div
      style={{
        padding: '0 16px 16px',
        borderTop: '0.5px solid var(--nav-border)',
        marginTop: '16px',
      }}
    >
      <div
        style={{
          fontSize: '9px',
          color: 'var(--text-tertiary)',
          textTransform: 'uppercase',
          letterSpacing: '.1em',
          fontFamily: 'var(--mono-font)',
          padding: '12px 0 10px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        Claim gravity model
        <span
          style={{
            fontSize: '9px',
            color: 'rgba(147,197,253,0.5)',
            fontStyle: 'italic',
          }}
        >
          — drag nodes · click to inspect
        </span>
      </div>

      <svg
        ref={svgRef}
        style={{
          width: '100%',
          borderRadius: '10px',
          display: 'block',
        }}
      />

      {selected && (
        <div
          style={{
            marginTop: '10px',
            padding: '10px 12px',
            background: 'rgba(15,23,42,0.9)',
            border: `0.5px solid ${selected.color}44`,
            borderLeft: `3px solid ${selected.color}`,
            borderRadius: '8px',
            fontSize: '11px',
            color: '#e2e8f0',
            fontFamily: 'var(--mono-font)',
          }}
        >
          <div
            style={{
              fontSize: '9px',
              color: selected.color,
              textTransform: 'uppercase',
              letterSpacing: '.08em',
              marginBottom: '4px',
            }}
          >
            {selected.type}
          </div>
          {selected.detail}
        </div>
      )}
    </div>
  );
}
