import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Upload, ShieldCheck, Play, Trash2, ArrowLeft, Clock, PlusSquare, RefreshCw, Activity } from 'lucide-react';
import ExtractionResults from './components/ExtractionResults';
import DiscrepancyDashboard from './components/DiscrepancyDashboard';
import BenchmarkingDashboard from './components/BenchmarkingDashboard';
import logo from './assets/logo.jpg';
import { Worker, Viewer } from '@react-pdf-viewer/core';
import '@react-pdf-viewer/core/lib/styles/index.css';
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
  const selectedFieldRef = useRef(selectedField);
  selectedFieldRef.current = selectedField; // sync during render so renderPageLayer reads current value

  const jumpPlugin = useMemo(() => ({
    install: (pluginFunctions) => {
      jumpToPageRef.current = pluginFunctions.jumpToPage;
    },
  }), []);

  useEffect(() => {
    if (!selectedField || !bboxMap || !jumpToPageRef.current) return;
    const entry = bboxMap[selectedField];
    if (!entry?.page) return;
    setTimeout(() => jumpToPageRef.current(entry.page - 1), 50);
  }, [selectedField]);

  const bboxPluginInstance = bboxPlugin({ bboxMap, selectedFieldRef });

  return (
    <div style={{ height: '100%', width: '100%', overflow: 'hidden' }}>
      <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.4.120/build/pdf.worker.min.js">
        <div style={{ height: '100%', border: '1px solid var(--border-color)', borderRadius: '8px', overflow: 'hidden', background: '#334155' }}>
          <Viewer fileUrl={pdfUrl} plugins={[bboxPluginInstance, jumpPlugin]} />
        </div>
      </Worker>
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
      
      let endpoint = 'http://127.0.0.1:8000/api/extract/police-report';
      if (item.type === 'ia') {
        endpoint = 'http://127.0.0.1:8000/api/extract/ia-report';
      } else if (item.type === 'acord') {
        endpoint = 'http://127.0.0.1:8000/api/extract/acord-report';
      } else if (item.type === 'hsmv') {
        endpoint = 'http://127.0.0.1:8000/api/extract/hsmv-report';
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
      
      let endpoint = 'http://127.0.0.1:8000/api/extract/police-report';
      if (target.type === 'ia') {
        endpoint = 'http://127.0.0.1:8000/api/extract/ia-report';
      } else if (target.type === 'acord') {
        endpoint = 'http://127.0.0.1:8000/api/extract/acord-report';
      } else if (target.type === 'hsmv') {
        endpoint = 'http://127.0.0.1:8000/api/extract/hsmv-report';
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
      <div className="master-detail-layout fade-in">
        <div className="sidebar" style={{ width: '400px' }}>
          <div className="sidebar-header" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <label className="btn-secondary" style={{ width: '100%', justifyContent: 'center' }}>
              <PlusSquare size={16} /> Add More Documents
              <input type="file" accept=".pdf" multiple onChange={handleFileSelect} disabled={isProcessing} style={{ display: 'none' }} />
            </label>
            
            <button 
              className="btn-primary" 
              onClick={runExtraction} 
              disabled={isProcessing}
            >
              {isProcessing ? (
                <><div className="spinner" style={{ width: '18px', height: '18px', borderWidth: '2px' }}></div> Processing {stagedFiles.length} Document(s)...</>
              ) : (
                <><Play size={18} /> Run Extraction ({stagedFiles.length})</>
              )}
            </button>
          </div>
          
          <div className="doc-list">
            {stagedFiles.map((file) => (
              <div 
                key={file.id} 
                className={`doc-item ${selectedFile.id === file.id ? 'active' : ''}`}
                onClick={() => setSelectedResultId(file.id)}
                style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div className="doc-item-title" title={file.name} style={{ margin: 0, maxWidth: '200px' }}>{file.name}</div>
                  <button 
                    style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', padding: '0.2rem' }}
                    onClick={(e) => { e.stopPropagation(); removeFile(file.id); }}
                    disabled={isProcessing}
                    title="Remove File"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
                <div style={{ display: 'flex', alignItems: 'center' }} onClick={e => e.stopPropagation()}>
                  <select 
                    className="type-select" 
                    value={file.type} 
                    onChange={(e) => updateFileType(file.id, e.target.value)}
                    disabled={isProcessing}
                    style={{ width: '100%', marginRight: 0, padding: '0.25rem' }}
                  >
                    <option value="ia">IA Report</option>
                    <option value="police">Police Report</option>
                    <option value="acord">ACORD Form</option>
                    <option value="hsmv">FL HSMV 90010S</option>
                  </select>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="detail-view" style={{ flexDirection: 'column' }}>
          {isProcessing && (
            <div style={{ padding: '1.5rem', background: 'var(--secondary-bg)', borderBottom: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', color: 'var(--text-main)' }}>
                <strong><div className="spinner" style={{ width: '14px', height: '14px', borderWidth: '2px', marginRight: '8px' }}></div> Extracting Documents...</strong>
                <span>{processingProgress.current} of {processingProgress.total}</span>
              </div>
              <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${(processingProgress.current / processingProgress.total) * 100}%`, background: 'var(--accent)', transition: 'width 0.3s ease' }}></div>
              </div>
            </div>
          )}
          {selectedFile ? (
            <div className="pane left-pane" style={{ borderRight: 'none', flex: 1, overflow: 'hidden' }}>
              <h3 style={{ marginTop: 0, marginBottom: '1rem', color: 'var(--text-muted)' }}>Document Preview</h3>
              <ErrorBoundary>
                <PDFViewer pdfUrl={selectedFile.pdfUrl} searchText={pdfSearchText} />
              </ErrorBoundary>
            </div>
          ) : null}
        </div>
      </div>
    );
  };

  const renderMasterDetailView = () => {
    const selectedResult = processedResults.find(r => r.id === selectedResultId);

    return (
      <div className="master-detail-layout fade-in">
        <div className="sidebar">
          <div className="sidebar-header" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <button className="btn-secondary" onClick={() => { setActiveView('upload'); setIsCrossReferencing(false); }} style={{ width: '100%', justifyContent: 'center' }}>
              <ArrowLeft size={16} /> Back to Upload
            </button>
            {processedResults.length >= 2 && (
              <button className="btn-primary" onClick={() => setIsCrossReferencing(true)} style={{ width: '100%', justifyContent: 'center', background: 'var(--accent)', border: 'none' }}>
                <RefreshCw size={16} /> Cross-Reference Claim
              </button>
            )}
            {processedResults.length > 0 && (
              <button className="btn-secondary" onClick={() => { setProcessedResults([]); setSelectedResultId(null); setActiveView('upload'); setIsCrossReferencing(false); }} style={{ width: '100%', justifyContent: 'center', color: 'var(--danger)', borderColor: 'rgba(239, 68, 68, 0.3)' }}>
                <Trash2 size={16} /> Clear History
              </button>
            )}
          </div>
          <div className="doc-list">
            {processedResults.length === 0 ? (
              <div style={{ padding: '2rem 1rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                No document history found.
              </div>
            ) : (
              processedResults.map(res => (
                <div 
                  key={res.id} 
                  className={`doc-item ${selectedResultId === res.id ? 'active' : ''}`}
                  onClick={() => { setSelectedResultId(res.id); setSelectedField(null); }}
                >
                  <div className="doc-item-title" title={res.name}>{res.name}</div>
                  <div className="doc-item-meta" style={{ marginBottom: '0.25rem' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{res.timestamp}</span>
                  </div>
                  <div className="doc-item-meta">
                    <span>{res.type === 'ia' ? 'IA Report' : res.type === 'acord' ? 'ACORD Form' : res.type === 'hsmv' ? 'FL HSMV 90010S' : 'Police Report'}</span>
                    <span className={`status-badge ${res.status}`}>{res.status === 'success' ? 'Extracted' : 'Failed'}</span>
                  </div>
                </div>
              ))
            )}
          </div>
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
