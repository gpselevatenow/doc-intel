import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Upload, ShieldCheck, Play, Trash2, ArrowLeft, Clock, PlusSquare, RefreshCw, Activity, Search, X, ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from 'lucide-react';
import ExtractionResults from './components/ExtractionResults';
import DiscrepancyDashboard from './components/DiscrepancyDashboard';
import BenchmarkingDashboard from './components/BenchmarkingDashboard';
import logo from './assets/logo.jpg';
import { Worker, Viewer } from '@react-pdf-viewer/core';
import '@react-pdf-viewer/core/lib/styles/index.css';
import { searchPlugin } from '@react-pdf-viewer/search';
import '@react-pdf-viewer/search/lib/styles/index.css';
import { bboxPlugin } from './components/BboxPlugin';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', color: 'var(--danger)', background: 'var(--card-bg)', height: '100%' }}>
          <h3>PDF Viewer Crashed</h3>
          <p>{this.state.error.toString()}</p>
          <pre style={{ fontSize: '0.8rem', whiteSpace: 'pre-wrap' }}>{this.state.error.stack}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}

const PDFViewer = ({ pdfUrl, bboxMap, selectedField }) => {
  const jumpToPageRef = useRef(null);
  const zoomRef = useRef(null);
  const selectedFieldRef = useRef(selectedField);
  selectedFieldRef.current = selectedField;
  const [searchQuery, setSearchQuery] = useState('');
  const [scale, setScale] = useState(1.0);

  const jumpPlugin = useMemo(() => ({
    install: (pluginFunctions) => {
      jumpToPageRef.current = pluginFunctions.jumpToPage;
      zoomRef.current = pluginFunctions.zoom;
    },
  }), []);

  const searchPluginInstance = searchPlugin();
  const { highlight, clearHighlights } = searchPluginInstance;

  useEffect(() => {
    if (!selectedField || !bboxMap || !jumpToPageRef.current) return;
    const entry = bboxMap[selectedField];
    if (!entry?.page) return;
    setTimeout(() => jumpToPageRef.current(entry.page - 1), 50);
  }, [selectedField]);

  const handleSearch = () => {
    if (!searchQuery.trim()) { clearHighlights(); return; }
    highlight({ keyword: searchQuery });
  };

  const handleZoom = (delta) => {
    const next = Math.max(0.5, Math.min(3.0, scale + delta));
    setScale(next);
    if (zoomRef.current) zoomRef.current(next);
  };

  const bboxPluginInstance = bboxPlugin({ bboxMap, selectedFieldRef });

  return (
    <div style={{ height: '100%', width: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      {/* Toolbar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 10px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', flexShrink: 0 }}>
        <input
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
          placeholder="Search in document…"
          style={{ flex: 1, border: '1px solid #e2e8f0', borderRadius: '5px', padding: '4px 8px', fontSize: '12px', color: '#111827', background: '#ffffff', outline: 'none' }}
        />
        <button onClick={handleSearch} title="Search" style={{ background: 'none', border: '1px solid #e2e8f0', borderRadius: '5px', padding: '4px 7px', cursor: 'pointer', color: '#6b7280', display: 'flex', alignItems: 'center' }}><Search size={13} /></button>
        <button onClick={() => { clearHighlights(); setSearchQuery(''); }} title="Clear" style={{ background: 'none', border: '1px solid #e2e8f0', borderRadius: '5px', padding: '4px 7px', cursor: 'pointer', color: '#6b7280', display: 'flex', alignItems: 'center' }}><X size={13} /></button>
        <div style={{ width: '1px', height: '20px', background: '#e2e8f0', margin: '0 2px' }} />
        <button onClick={() => handleZoom(-0.1)} title="Zoom out" style={{ background: 'none', border: '1px solid #e2e8f0', borderRadius: '5px', padding: '4px 7px', cursor: 'pointer', color: '#6b7280', display: 'flex', alignItems: 'center' }}><ZoomOut size={13} /></button>
        <span style={{ fontSize: '11px', color: '#6b7280', minWidth: '38px', textAlign: 'center' }}>{Math.round(scale * 100)}%</span>
        <button onClick={() => handleZoom(0.1)} title="Zoom in" style={{ background: 'none', border: '1px solid #e2e8f0', borderRadius: '5px', padding: '4px 7px', cursor: 'pointer', color: '#6b7280', display: 'flex', alignItems: 'center' }}><ZoomIn size={13} /></button>
      </div>
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.4.120/build/pdf.worker.min.js">
          <div style={{ height: '100%', border: '1px solid var(--border-color)', borderRadius: '8px', overflow: 'hidden', background: '#334155' }}>
            <Viewer fileUrl={pdfUrl} plugins={[bboxPluginInstance, jumpPlugin, searchPluginInstance]} />
          </div>
        </Worker>
      </div>
    </div>
  );
};

function App() {
  const [activeView, setActiveView] = useState('upload'); // 'upload', 'results', 'history'
  const [stagedFiles, setStagedFiles] = useState([]);
  const [processedResults, setProcessedResults] = useState([]);
  const [selectedResultId, setSelectedResultId] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState({ current: 0, total: 0 });
  const [selectedField, setSelectedField] = useState(null);
  const [isCrossReferencing, setIsCrossReferencing] = useState(false);
  const [pdfSearchText, setPdfSearchText] = useState('');
  const [isReprocessingId, setIsReprocessingId] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // --- Upload Handlers ---
  const handleFileSelect = (event) => {
    const newFiles = Array.from(event.target.files).filter(f => f.type === 'application/pdf');
    if (newFiles.length === 0) return;

    if (stagedFiles.length + newFiles.length > 10) {
      alert('You can only upload up to 10 documents at a time.');
      return;
    }

    const newStaged = newFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      name: file.name,
      type: file.name.replace(/[_.\-]/g, ' ').match(/\b(ia|property|adjuster)\b/i) ? 'ia'
           : file.name.replace(/[_.\-]/g, ' ').match(/\bacord\b/i) ? 'acord'
           : /hsmv|90010/i.test(file.name) ? 'hsmv'
           : 'police',
      pdfUrl: URL.createObjectURL(file)
    }));

    setStagedFiles(prev => [...prev, ...newStaged]);
  };

  const updateFileType = (id, type) => {
    setStagedFiles(prev => prev.map(f => f.id === id ? { ...f, type } : f));
  };

  const removeFile = (id) => {
    setStagedFiles(prev => prev.filter(f => f.id !== id));
  };

  // --- Processing ---
  const runExtraction = async () => {
    if (stagedFiles.length === 0) return;
    setIsProcessing(true);
    setProcessingProgress({ current: 0, total: stagedFiles.length });
    
    const newResults = [];

    for (let i = 0; i < stagedFiles.length; i++) {
      const item = stagedFiles[i];
      setProcessingProgress({ current: i + 1, total: stagedFiles.length });
      
      const formData = new FormData();
      formData.append('file', item.file);
      
      let endpoint = 'http://127.0.0.1:8001/api/extract/police-report';
      if (item.type === 'ia') {
        endpoint = 'http://127.0.0.1:8001/api/extract/ia-report';
      } else if (item.type === 'acord') {
        endpoint = 'http://127.0.0.1:8001/api/extract/acord-report';
      } else if (item.type === 'hsmv') {
        endpoint = 'http://127.0.0.1:8001/api/extract/hsmv-report';
      }
        
      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          body: formData,
        });
        const data = await response.json();
        
        newResults.push({
          id: item.id,
          name: item.name,
          type: item.type,
          data,
          pdfUrl: item.pdfUrl,
          status: 'success',
          timestamp: new Date().toLocaleString()
        });
      } catch (error) {
        console.error('Error extracting data for', item.name, error);
        newResults.push({
          id: item.id,
          name: item.name,
          type: item.type,
          data: null,
          pdfUrl: item.pdfUrl,
          status: 'error',
          timestamp: new Date().toLocaleString()
        });
      }
    }

    // Prepend new results to history
    setProcessedResults(prev => [...newResults, ...prev]);
    // Clear staged files
    setStagedFiles([]);
    setIsProcessing(false);
    
    // Switch to results view and select first processed item
    if (newResults.length > 0) {
      setSelectedResultId(newResults[0].id);
      setActiveView('results');
    }
  };

  const reprocessResult = async (resultId) => {
    const target = processedResults.find(r => r.id === resultId);
    if (!target) return;
    
    setIsReprocessingId(resultId);
    
    try {
      const res = await fetch(target.pdfUrl);
      const blob = await res.blob();
      const file = new File([blob], target.name, { type: 'application/pdf' });
      
      const formData = new FormData();
      formData.append('file', file);
      
      let endpoint = 'http://127.0.0.1:8001/api/extract/police-report';
      if (target.type === 'ia') {
        endpoint = 'http://127.0.0.1:8001/api/extract/ia-report';
      } else if (target.type === 'acord') {
        endpoint = 'http://127.0.0.1:8001/api/extract/acord-report';
      } else if (target.type === 'hsmv') {
        endpoint = 'http://127.0.0.1:8001/api/extract/hsmv-report';
      }
      
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });
      const newData = await response.json();
      
      setProcessedResults(prev => prev.map(r => r.id === resultId ? {
        ...r,
        data: newData,
        status: 'success',
        timestamp: new Date().toLocaleString()
      } : r));
    } catch (error) {
      console.error('Error reprocessing data for', target.name, error);
      alert('Failed to rerun extraction. Please try again.');
    } finally {
      setIsReprocessingId(null);
    }
  };

  // --- Render Helpers ---
  const renderHeader = () => (
    <nav style={{
      background: 'var(--nav-bg)',
      borderBottom: '0.5px solid var(--nav-border)',
      height: '48px',
      display: 'flex',
      alignItems: 'center',
      padding: '0 24px',
      gap: '0',
      flexShrink: 0,
    }}>
      <div style={{ display:'flex', alignItems:'center', gap:'8px', marginRight:'32px' }}>
        <div style={{
          background: '#4f46e5', color: 'white',
          fontSize: '10px', fontWeight: '600',
          padding: '3px 7px', borderRadius: '4px',
          letterSpacing: '.02em', fontFamily: 'var(--mono-font)',
        }}>EN</div>
        <span style={{ color:'#e2e8f0', fontSize:'14px', fontWeight:'500' }}>Doc Intel</span>
      </div>

      {[
        { id:'upload', icon:<PlusSquare size={13}/>, label:'New extraction' },
        { id:'history', icon:<Clock size={13}/>, label:'History' },
        { id:'benchmarks', icon:<Activity size={13}/>, label:'Benchmarks' },
      ].map(item => (
        <div key={item.id} onClick={() => setActiveView(item.id)}
          style={{
            padding: '0 16px',
            height: '48px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
            color: (item.id === 'history' && (activeView === 'history' || activeView === 'results'))
              ? 'var(--accent)'
              : activeView === item.id ? 'var(--accent)' : 'var(--text-tertiary)',
            borderBottom: (item.id === 'history' && (activeView === 'history' || activeView === 'results'))
              ? '2px solid var(--accent)'
              : activeView === item.id ? '2px solid var(--accent)' : '2px solid transparent',
            cursor: 'pointer',
            transition: 'color 0.15s',
            userSelect: 'none',
          }}>
          {item.icon}{item.label}
        </div>
      ))}

      <div style={{ flex:1 }} />

      <div style={{ display:'flex', alignItems:'center', gap:'6px', fontSize:'11px', color:'var(--success-bright)', fontFamily:'var(--mono-font)' }}>
        <div style={{ width:'6px', height:'6px', borderRadius:'50%', background:'var(--success-bright)' }} />
        System online · F1 1.0000
      </div>
    </nav>
  );

  const renderUploadView = () => {
    if (stagedFiles.length === 0) {
      return (
        <div style={{ display:'flex', flexDirection:'column', height:'100%', background:'var(--surface-1)', overflowY:'auto' }}>
          {/* Hero */}
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'32px', padding:'48px 48px 32px' }}>
            {/* Left: copy + stats */}
            <div>
              <div style={{ fontSize:'10px', color:'var(--accent)', letterSpacing:'.12em', textTransform:'uppercase', fontFamily:'var(--mono-font)', marginBottom:'12px' }}>
                Claims intelligence · v0.9
              </div>
              <h2 style={{ fontSize:'26px', fontWeight:'500', color:'#f1f5f9', lineHeight:'1.3', marginBottom:'10px', marginTop:0 }}>
                Extract. Validate.<br/>Act on claims data.
              </h2>
              <p style={{ fontSize:'13px', color:'var(--text-tertiary)', lineHeight:'1.7', maxWidth:'380px', margin:0 }}>
                Upload police reports or IA adjuster documents. The system classifies, extracts 17+ fields, flags reserve language, and reconstructs the claim timeline — automatically.
              </p>
              <div style={{ display:'flex', gap:'24px', marginTop:'24px' }}>
                {[
                  { n:'1.0000', l:'F1 score' },
                  { n:'17', l:'Fields extracted' },
                  { n:'5 / 5', l:'States validated' },
                ].map(s => (
                  <div key={s.l}>
                    <div style={{ fontSize:'22px', fontWeight:'500', color:'var(--accent)', fontFamily:'var(--mono-font)' }}>{s.n}</div>
                    <div style={{ fontSize:'10px', color:'var(--text-tertiary)', textTransform:'uppercase', letterSpacing:'.08em', marginTop:'2px' }}>{s.l}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: drop zone */}
            <label style={{ border:'1px dashed var(--accent-border)', borderRadius:'12px', padding:'32px', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', gap:'10px', cursor:'pointer', background:'var(--accent-bg)', transition:'border-color 0.2s, background 0.2s' }}>
              <div style={{ width:'44px', height:'44px', borderRadius:'10px', background:'var(--accent-bg)', border:'0.5px solid var(--accent-border)', display:'flex', alignItems:'center', justifyContent:'center', color:'var(--accent)' }}>
                <Upload size={20} />
              </div>
              <div style={{ fontSize:'14px', fontWeight:'500', color:'#e2e8f0' }}>Drop documents here</div>
              <div style={{ fontSize:'12px', color:'var(--text-tertiary)' }}>or click to browse — up to 10 files</div>
              <div style={{ display:'flex', gap:'8px', marginTop:'4px' }}>
                {[
                  { l:'Police report', c:'var(--accent)', bg:'var(--accent-bg)', bc:'var(--accent-border)' },
                  { l:'IA report', c:'var(--success-bright)', bg:'var(--success-bg)', bc:'var(--success-border)' },
                  { l:'ACORD', c:'var(--warning)', bg:'rgba(245,158,11,0.08)', bc:'rgba(245,158,11,0.3)' },
                ].map(t => (
                  <div key={t.l} style={{ padding:'3px 8px', borderRadius:'4px', fontSize:'10px', border:`0.5px solid ${t.bc}`, background:t.bg, color:t.c, fontFamily:'var(--mono-font)' }}>{t.l}</div>
                ))}
              </div>
              <input type="file" accept=".pdf" multiple style={{ display:'none' }} onChange={handleFileSelect} />
            </label>
          </div>

          {/* Recent extractions */}
          {processedResults.length > 0 && (
            <div>
              <div style={{ fontSize:'10px', color:'var(--text-tertiary)', letterSpacing:'.1em', textTransform:'uppercase', padding:'14px 48px 8px', borderTop:'0.5px solid var(--nav-border)', fontFamily:'var(--mono-font)' }}>
                Recent extractions
              </div>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:'1px', background:'var(--nav-border)', borderTop:'0.5px solid var(--nav-border)' }}>
                {processedResults.slice(0,6).map(r => (
                  <div key={r.id}
                    onClick={() => { setSelectedResultId(r.id); setActiveView('results'); }}
                    style={{ padding:'14px 20px', background:'var(--surface-1)', cursor:'pointer', transition:'background 0.15s' }}
                    onMouseEnter={e => e.currentTarget.style.background='var(--surface-3)'}
                    onMouseLeave={e => e.currentTarget.style.background='var(--surface-1)'}
                  >
                    <div style={{ fontSize:'11px', color:'#cbd5e1', fontFamily:'var(--mono-font)', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis', marginBottom:'6px' }}>{r.name}</div>
                    <div style={{ display:'flex', alignItems:'center', gap:'8px' }}>
                      <div style={{ fontSize:'9px', padding:'1px 6px', borderRadius:'3px', fontFamily:'var(--mono-font)', background: r.type === 'ia' ? 'var(--success-bg)' : 'var(--accent-bg)', color: r.type === 'ia' ? 'var(--success-bright)' : 'var(--accent)' }}>
                        {r.type === 'ia' ? 'IA' : r.type === 'acord' ? 'ACORD' : r.type === 'hsmv' ? 'HSMV' : 'Police'}
                      </div>
                      <div style={{ fontSize:'10px', color:'var(--text-tertiary)' }}>{r.timestamp}</div>
                      <div style={{ marginLeft:'auto', fontSize:'11px', color:'var(--success-bright)', fontFamily:'var(--mono-font)' }}>
                        {r.data?.accuracy_score ? `${r.data.accuracy_score.toFixed(1)}%` : '—'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      );
    }

    const selectedFile = stagedFiles.find(f => f.id === selectedResultId) || stagedFiles[0];

    return (
      <div style={{ display: 'flex', width: '100%', height: '100%', background: 'var(--surface-1)' }}>
        <div style={{ width: '280px', flexShrink: 0, background: 'var(--surface-2)', borderRight: '0.5px solid var(--nav-border)', display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', padding: '14px 12px', gap: '8px' }}>
          <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', padding: '8px 12px', background: 'transparent', border: '0.5px solid var(--nav-border)', borderRadius: '6px', color: 'var(--text-muted)', fontSize: '12px', cursor: 'pointer', width: '100%', boxSizing: 'border-box' }}>
            <PlusSquare size={13} /> Add more documents
            <input type="file" accept=".pdf" multiple onChange={handleFileSelect} disabled={isProcessing} style={{ display: 'none' }} />
          </label>

          <button
            onClick={runExtraction}
            disabled={isProcessing}
            style={{ background: isProcessing ? 'rgba(147,197,253,0.1)' : '#93c5fd', color: isProcessing ? '#93c5fd' : '#0a1628', border: '0.5px solid #93c5fd', borderRadius: '6px', padding: '9px 16px', fontSize: '12px', fontWeight: '600', fontFamily: 'var(--mono-font)', cursor: isProcessing ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', width: '100%' }}
          >
            {isProcessing ? (
              <><RefreshCw size={12} style={{ animation: 'spin 1s linear infinite' }} /> Extracting...</>
            ) : (
              <><Play size={12} /> Run Extraction ({stagedFiles.length})</>
            )}
          </button>

          <div style={{ flex: 1, overflowY: 'auto', marginTop: '4px' }}>
            {stagedFiles.map((file) => (
              <div
                key={file.id}
                onClick={() => setSelectedResultId(file.id)}
                style={{ padding: '10px', borderRadius: '6px', cursor: 'pointer', borderLeft: file.id === selectedResultId ? '2px solid var(--accent)' : '2px solid transparent', background: file.id === selectedResultId ? 'var(--accent-bg)' : 'transparent', marginBottom: '2px' }}
              >
                <div style={{ fontSize: '11px', color: '#cbd5e1', fontFamily: 'var(--mono-font)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginBottom: '6px' }}>{file.name}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }} onClick={e => e.stopPropagation()}>
                  <select
                    value={file.type}
                    onChange={(e) => updateFileType(file.id, e.target.value)}
                    disabled={isProcessing}
                    style={{ flex: 1, background: 'var(--surface-1)', border: '0.5px solid var(--nav-border)', borderRadius: '4px', color: 'var(--text-muted)', fontSize: '11px', padding: '4px 6px', fontFamily: 'var(--mono-font)' }}
                  >
                    <option value="ia">IA Report</option>
                    <option value="police">Police Report</option>
                    <option value="acord">ACORD Form</option>
                    <option value="hsmv">FL HSMV 90010S</option>
                  </select>
                  <button
                    onClick={(e) => { e.stopPropagation(); removeFile(file.id); }}
                    disabled={isProcessing}
                    style={{ background: 'transparent', border: 'none', color: 'rgba(239,68,68,0.5)', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center' }}
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--surface-1)', overflow: 'hidden' }}>
          <div style={{ padding: '10px 16px', borderBottom: '0.5px solid var(--nav-border)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', fontFamily: 'var(--mono-font)' }}>Document preview</div>
            {selectedFile && (
              <div style={{ fontSize: '10px', color: 'var(--accent)', fontFamily: 'var(--mono-font)', marginLeft: '8px' }}>{selectedFile.name}</div>
            )}
          </div>
          {isProcessing && (
            <div style={{ padding: '12px 16px', borderBottom: '0.5px solid var(--nav-border)' }}>
              <div style={{ height: '3px', background: 'rgba(255,255,255,0.06)', borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${(processingProgress.current / processingProgress.total) * 100}%`, background: 'var(--accent)', borderRadius: '2px', transition: 'width 0.3s ease' }} />
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', fontFamily: 'var(--mono-font)', marginTop: '6px' }}>
                Extracting... {processingProgress.current} of {processingProgress.total}
              </div>
            </div>
          )}
          <div style={{ flex: 1, overflow: 'hidden', padding: '16px' }}>
            <ErrorBoundary>
              <PDFViewer pdfUrl={selectedFile?.pdfUrl} searchText={pdfSearchText} />
            </ErrorBoundary>
          </div>
        </div>
      </div>
    );
  };

  const renderMasterDetailView = () => {
    const selectedResult = processedResults.find(r => r.id === selectedResultId);

    return (
      <div className="master-detail-layout fade-in">
        <div style={{ width: sidebarCollapsed ? '40px' : '240px', flexShrink: 0, background: 'var(--surface-2)', borderRight: '0.5px solid var(--nav-border)', display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', transition: 'width 0.2s ease' }}>
          {/* Collapse toggle */}
          <div style={{ display: 'flex', justifyContent: sidebarCollapsed ? 'center' : 'flex-end', padding: '6px 8px', borderBottom: '0.5px solid var(--nav-border)', flexShrink: 0 }}>
            <button onClick={() => setSidebarCollapsed(c => !c)} title={sidebarCollapsed ? 'Expand' : 'Collapse'}
              style={{ background: 'transparent', border: '0.5px solid var(--nav-border)', borderRadius: '4px', padding: '3px 6px', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', alignItems: 'center' }}>
              {sidebarCollapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
            </button>
          </div>
          {!sidebarCollapsed && (
            <>
              <div style={{ padding: '12px', borderBottom: '0.5px solid var(--nav-border)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <button onClick={() => setActiveView('upload')}
                  style={{ background: 'transparent', border: '0.5px solid var(--nav-border)', borderRadius: '6px', color: 'var(--text-muted)', fontSize: '11px', padding: '7px 12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', width: '100%' }}>
                  <ArrowLeft size={12} /> New extraction
                </button>
              </div>
              <div style={{ padding: '10px 14px 6px', fontSize: '9px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', fontFamily: 'var(--mono-font)' }}>Extractions</div>
              <div style={{ flex: 1, overflowY: 'auto' }}>
                {processedResults.map(r => (
                  <div key={r.id}
                    onClick={() => { setSelectedResultId(r.id); setSelectedField(null); }}
                    style={{ padding: '11px 14px', borderBottom: '0.5px solid var(--nav-border)', cursor: 'pointer', borderLeft: r.id === selectedResultId ? '2px solid var(--accent)' : '2px solid transparent', background: r.id === selectedResultId ? 'var(--accent-bg)' : 'transparent', transition: 'background 0.15s' }}>
                    <div style={{ fontSize: '11px', color: '#cbd5e1', fontFamily: 'var(--mono-font)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginBottom: '5px' }}>{r.name}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <div style={{ fontSize: '9px', padding: '1px 5px', borderRadius: '3px', fontFamily: 'var(--mono-font)', background: r.type === 'ia' ? 'var(--success-bg)' : 'var(--accent-bg)', color: r.type === 'ia' ? 'var(--success-bright)' : 'var(--accent)' }}>
                        {r.type === 'ia' ? 'IA' : r.type === 'acord' ? 'ACORD' : r.type === 'hsmv' ? 'HSMV' : 'Police'}
                      </div>
                      <div style={{ marginLeft: 'auto', fontSize: '10px', color: 'var(--success-bright)', fontFamily: 'var(--mono-font)' }}>
                        {r.data?.accuracy_score ? `${r.data.accuracy_score.toFixed(1)}%` : '—'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ padding: '10px 12px', borderTop: '0.5px solid var(--nav-border)' }}>
                <button onClick={() => { setProcessedResults([]); setSelectedResultId(null); setActiveView('upload'); setIsCrossReferencing(false); }}
                  style={{ background: 'transparent', border: '0.5px solid rgba(239,68,68,0.2)', borderRadius: '6px', color: 'rgba(239,68,68,0.6)', fontSize: '11px', padding: '6px 12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', width: '100%' }}>
                  <Trash2 size={11} /> Clear history
                </button>
              </div>
            </>
          )}
        </div>

        <div className="detail-view">
          {isCrossReferencing ? (
            <div style={{ flex: 1, overflowY: 'auto', background: 'var(--bg-color)' }}>
              <DiscrepancyDashboard 
                iaData={processedResults.find(r => r.type === 'ia')?.data || {}} 
                policeData={processedResults.find(r => r.type === 'police')?.data || {}} 
                onClose={() => setIsCrossReferencing(false)} 
              />
            </div>
          ) : selectedResult ? (
            <>
              <div className="pane left-pane" style={{ overflow: 'hidden' }}>
                <ErrorBoundary>
                  <PDFViewer 
                    pdfUrl={selectedResult.pdfUrl} 
                    bboxMap={selectedResult.data?.bbox_map || {}}
                    selectedField={selectedField} 
                  />
                </ErrorBoundary>
              </div>
              <div className="pane right-pane">
                {selectedResult.status === 'success' ? (
                  <ExtractionResults
                    key={selectedResultId}
                    type={selectedResult.type}
                    data={selectedResult.data}
                    docId={selectedResult.name}
                    onFieldClick={(fieldId) => setSelectedField(fieldId)}
                    selectedField={selectedField}
                    isReprocessing={isReprocessingId === selectedResult.id}
                    onReprocess={() => reprocessResult(selectedResult.id)}
                  />
                ) : (
                  <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--danger)' }}>
                    Failed to extract data. The backend server might be unreachable or the document is invalid.
                  </div>
                )}
              </div>
            </>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', color: 'var(--text-muted)' }}>
              Select a document from the sidebar to view results.
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="app-container">
      {renderHeader()}
      <main className="main-content">
        {activeView === 'benchmarks' ? (
          <BenchmarkingDashboard />
        ) : activeView === 'upload' ? (
          renderUploadView()
        ) : (
          renderMasterDetailView()
        )}
      </main>
    </div>
  );
}

export default App;
