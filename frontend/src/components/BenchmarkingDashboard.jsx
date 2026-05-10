import React, { useState } from 'react';
import { Activity, Zap, Cpu, CheckCircle, Database, AlertCircle } from 'lucide-react';

export default function BenchmarkingDashboard() {
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);

  const runBenchmark = async () => {
    setLoading(true);
    setError(null);
    try {
      // Small artificial delay so the user can see the loading state in the demo
      await new Promise(resolve => setTimeout(resolve, 800));
      const res = await fetch('http://localhost:8000/api/benchmark/run');
      if (!res.ok) throw new Error("Failed to reach backend");
      const data = await res.json();
      
      if (data.status === "success") {
        setMetrics(data);
      } else {
        throw new Error(data.message || "Unknown error");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pane fade-in" style={{ padding: '2rem', flex: 1, overflowY: 'auto' }}>
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <div>
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
              <Activity size={24} color="var(--accent)" /> System Diagnostics & Benchmarks
            </h2>
            <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>
              Run deterministic load testing across the Local VPC NLP engine.
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
          <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--danger)', borderRadius: '8px', color: 'var(--danger)', marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertCircle size={20} /> {error}
          </div>
        )}

        {!metrics && !loading && !error && (
          <div style={{ padding: '4rem 2rem', textAlign: 'center', background: 'var(--card-bg)', borderRadius: '12px', border: '1px dashed var(--border-color)' }}>
            <Activity size={48} color="var(--border-color)" style={{ marginBottom: '1rem' }} />
            <h3 style={{ color: 'var(--text-muted)' }}>Ready to run benchmarks</h3>
            <p style={{ color: 'var(--text-muted)' }}>Click the button above to simulate 50 extraction pipelines and pull human-in-the-loop metrics.</p>
          </div>
        )}

        {metrics && (
          <div className="fade-in" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>
            
            {/* Card 1: Latency */}
            <div style={{ background: 'var(--card-bg)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                <Cpu size={20} /> <span style={{ fontWeight: 600 }}>Average Latency</span>
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 700, color: '#10b981' }}>
                {metrics.avg_latency_ms} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>ms / doc</span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem', lineHeight: 1.4 }}>
                Time required for the Deterministic NLP engine to parse the layout and extract variables.
              </p>
            </div>

            {/* Card 2: Throughput */}
            <div style={{ background: 'var(--card-bg)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                <Zap size={20} /> <span style={{ fontWeight: 600 }}>Throughput</span>
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 700, color: '#3b82f6' }}>
                {metrics.throughput_per_sec} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>docs / sec</span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem', lineHeight: 1.4 }}>
                Simulated execution of {metrics.iterations} documents in {metrics.total_time_sec} seconds.
              </p>
            </div>

            {/* Card 3: Human-in-the-loop */}
            <div style={{ background: 'var(--card-bg)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                <Database size={20} /> <span style={{ fontWeight: 600 }}>Operational Efficiency</span>
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 700, color: '#f59e0b' }}>
                {metrics.correction_count} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>corrections</span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem', lineHeight: 1.4 }}>
                Total adjuster overrides logged securely to the local SQLite VPC database for future regex tuning.
              </p>
            </div>

          </div>
        )}
      </div>
    </div>
  );
}
