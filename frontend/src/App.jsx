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
  const bboxPluginInstance = bboxPlugin({ bboxMap, selectedField });

  return (
    <div style={{ height: '100%', width: '100%', overflow: 'hidden' }}>
      <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.4.120/build/pdf.worker.min.js">
        <div style={{ height: '100%', border: '1px solid var(--border-color)', borderRadius: '8px', overflow: 'hidden', background: '#334155' }}>
          <Viewer fileUrl={pdfUrl} plugins={[bboxPluginInstance]} />
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
    <header className="header">
      <div className="header-left" style={{ gap: '0.75rem', alignItems: 'center' }}>
        <img src={logo} alt="Elevatenow Logo" style={{ height: '24px', borderRadius: '4px', objectFit: 'contain' }} />
        <h1>Doc Intel</h1>
      </div>
      <div className="nav-tabs">
        <button 
          className={`nav-tab ${activeView === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveView('upload')}
        >
          <PlusSquare size={18} /> New Extraction
        </button>
        <button 
          className={`nav-tab ${(activeView === 'history' || activeView === 'results') ? 'active' : ''}`}
          onClick={() => setActiveView('history')}
        >
          <Clock size={18} /> History
        </button>
        <button 
          className={`nav-tab ${activeView === 'benchmarks' ? 'active' : ''}`}
          onClick={() => setActiveView('benchmarks')}
        >
          <Activity size={18} /> System Benchmarks
        </button>
      </div>
    </header>
  );

  const renderUploadView = () => {
    if (stagedFiles.length === 0) {
      return (
        <div className="upload-view fade-in">
          <h2>Process New Documents</h2>
          <p style={{ color: 'var(--text-muted)' }}>Upload up to 10 PDF documents. Select the report type for each before running the extraction.</p>
          
          <label className="upload-area">
            <Upload size={40} style={{ marginBottom: '1rem', color: 'var(--accent)' }} />
            <h3>Click to Select PDFs</h3>
            <p>Supports up to 10 files simultaneously</p>
            <input type="file" accept=".pdf" multiple onChange={handleFileSelect} disabled={isProcessing} />
          </label>
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
                    type={selectedResult.type} 
                    data={selectedResult.data} 
                    docId={selectedResult.name}
                    onFieldClick={(fieldId) => setSelectedField(fieldId)}
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
