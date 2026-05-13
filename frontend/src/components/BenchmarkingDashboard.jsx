import React, { useState, useEffect } from 'react';
import { Activity, Zap, Cpu, CheckCircle, Database, AlertCircle, TrendingDown, Clock } from 'lucide-react';

export default function BenchmarkingDashboard() {
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);
  const [failures, setFailures] = useState(null);
  const [failuresLoading, setFailuresLoading] = useState(true);

  useEffect(() => {
    fetchFailures();
  }, []);

  const fetchFailures = async () => {
    setFailuresLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/benchmark/failures');
      if (!res.ok) throw new Error('Failed to reach backend');
      const data = await res.json();
      if (data.status === 'success') setFailures(data);
    } catch (e) {
      // Silent — failures panel is optional
    } finally {
      setFailuresLoading(false);
    }
  };

  const runBenchmark = async () => {
    setLoading(true);
    setError(null);
    try {
      await new Promise(resolve => setTimeout(resolve, 800));
      const res = await fetch('http://localhost:8000/api/benchmark/run');
      if (!res.ok) throw new Error('Failed to reach backend');
      const data = await res.json();
      if (data.status === 'success') {
        setMetrics(data);
        fetchFailures(); // refresh failure analytics after benchmark
      } else {
        throw new Error(data.message || 'Unknown error');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const barColor = (pct) => pct >= 70 ? '#ef4444' : pct >= 40 ? '#f59e0b' : '#10b981';

  return (
    <div className="pane fade-in" style={{ padding: '2rem', flex: 1, overflowY: 'auto' }}>
      <div style={{ maxWidth: '960px', margin: '0 auto' }}>

        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <div>
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
              <Activity size={24} color="var(--accent)" /> System Diagnostics & Benchmarks
            </h2>
            <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>
              Load testing + human-in-the-loop field failure analytics.
            </p>
          </div>
          <button
            className="btn-primary"
            onClick={runBenchmark}
            disabled={loading}
            style={{ padding: '0.75rem 1.5rem', fontSize: '1rem' }}
          >
            {loading ? (
              <><div className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }} /> Running Test...</>
            ) : (
              <><Zap size={18} /> Execute Benchmark</>
            )}
          </button>
        </div>

        {error && (
          <div style={{ padding: '1rem', background: 'rgba(239,68,68,0.1)', border: '1px solid var(--danger)', borderRadius: '8px', color: 'var(--danger)', marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertCircle size={20} /> {error}
          </div>
        )}

        {!metrics && !loading && !error && (
          <div style={{ padding: '3rem 2rem', textAlign: 'center', background: 'var(--card-bg)', borderRadius: '12px', border: '1px dashed var(--border-color)', marginBottom: '2rem' }}>
            <Activity size={48} color="var(--border-color)" style={{ marginBottom: '1rem' }} />
            <h3 style={{ color: 'var(--text-muted)' }}>Ready to run benchmarks</h3>
            <p style={{ color: 'var(--text-muted)' }}>Click Execute Benchmark to simulate 50 extraction pipelines.</p>
          </div>
        )}

        {metrics && (
          <div className="fade-in" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
            <div style={{ background: 'var(--card-bg)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                <Cpu size={20} /> <span style={{ fontWeight: 600 }}>Average Latency</span>
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 700, color: '#10b981' }}>
                {metrics.avg_latency_ms} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>ms / doc</span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem', lineHeight: 1.4 }}>
                Deterministic NLP engine parse + field extraction time.
              </p>
            </div>

            <div style={{ background: 'var(--card-bg)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                <Zap size={20} /> <span style={{ fontWeight: 600 }}>Throughput</span>
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 700, color: '#3b82f6' }}>
                {metrics.throughput_per_sec} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>docs / sec</span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem', lineHeight: 1.4 }}>
                {metrics.iterations} docs in {metrics.total_time_sec}s.
              </p>
            </div>

            <div style={{ background: 'var(--card-bg)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                <Database size={20} /> <span style={{ fontWeight: 600 }}>Total Corrections</span>
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 700, color: '#f59e0b' }}>
                {metrics.correction_count} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>overrides</span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem', lineHeight: 1.4 }}>
                Logged to SQLite; patterns learned and applied automatically.
              </p>
            </div>
          </div>
        )}

        {/* Field Failure Analytics */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>

          {/* Top corrected fields */}
          <div style={{ background: 'var(--card-bg)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: '0 0 1rem 0', fontSize: '1rem' }}>
              <TrendingDown size={18} color="var(--danger)" /> Top Corrected Fields
            </h3>
            {failuresLoading ? (
              <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)' }}>
                <div className="spinner" style={{ width: '20px', height: '20px', borderWidth: '2px', margin: '0 auto 0.5rem' }} />
                Loading...
              </div>
            ) : !failures || failures.top_failures.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                <CheckCircle size={32} color="var(--success)" style={{ marginBottom: '0.5rem' }} />
                <div>No corrections yet — extraction looks clean.</div>
              </div>
            ) : (
              <div>
                {failures.top_failures.map((f, i) => {
                  const total = failures.top_failures[0].correction_count || 1;
                  const pct = Math.round((f.correction_count / total) * 100);
                  return (
                    <div key={i} style={{ marginBottom: '0.85rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', fontSize: '0.85rem' }}>
                        <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{f.field}</span>
                        <span style={{ color: 'var(--text-muted)' }}>{f.correction_count} corrections</span>
                      </div>
                      <div style={{ height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${pct}%`, background: barColor(pct), transition: 'width 0.4s ease', borderRadius: '3px' }} />
                      </div>
                    </div>
                  );
                })}
                <div style={{ marginTop: '1rem', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  {failures.total_corrections} total corrections tracked · patterns auto-learned
                </div>
              </div>
            )}
          </div>

          {/* Recent corrections */}
          <div style={{ background: 'var(--card-bg)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: '0 0 1rem 0', fontSize: '1rem' }}>
              <Clock size={18} color="var(--accent)" /> Recent Corrections
            </h3>
            {failuresLoading ? (
              <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)' }}>
                <div className="spinner" style={{ width: '20px', height: '20px', borderWidth: '2px', margin: '0 auto 0.5rem' }} />
                Loading...
              </div>
            ) : !failures || failures.recent_corrections.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                <CheckCircle size={32} color="var(--success)" style={{ marginBottom: '0.5rem' }} />
                <div>No corrections logged yet.</div>
              </div>
            ) : (
              <div style={{ overflowY: 'auto', maxHeight: '280px' }}>
                {failures.recent_corrections.map((c, i) => (
                  <div key={i} style={{ padding: '0.6rem 0', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: '0.82rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.15rem' }}>
                      <span style={{ fontWeight: 700, color: 'var(--accent)' }}>{c.field}</span>
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{c.at.split('T')[0]}</span>
                    </div>
                    <div style={{ color: 'var(--danger)', textDecoration: 'line-through', opacity: 0.7 }} title="Original">
                      {c.from || '(empty)'}
                    </div>
                    <div style={{ color: 'var(--success)' }} title="Corrected to">
                      → {c.to}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
