import React from 'react';
import { AlertTriangle } from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ error, errorInfo });
    console.error("ErrorBoundary caught an error", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', background: '#222', color: 'white', minHeight: '100vh', fontFamily: 'monospace' }}>
          <div style={{ background: '#4a0000', padding: '2rem', borderRadius: '8px', border: '1px solid #ff4444' }}>
            <h1 style={{ display: 'flex', alignItems: 'center', gap: '1rem', color: '#ff4444' }}>
              <AlertTriangle size={32} /> Fatal React Error
            </h1>
            <p>The UI crashed completely. This replaces the blank white screen so we can debug.</p>
            <h2 style={{ marginTop: '2rem' }}>Error Message:</h2>
            <pre style={{ background: 'black', padding: '1rem', overflowX: 'auto', color: '#ffaaaa' }}>
              {this.state.error && this.state.error.toString()}
            </pre>
            <h2>Component Stack:</h2>
            <pre style={{ background: 'black', padding: '1rem', overflowX: 'auto', color: '#ccc' }}>
              {this.state.errorInfo && this.state.errorInfo.componentStack}
            </pre>
          </div>
        </div>
      );
    }

    return this.props.children; 
  }
}

export default ErrorBoundary;
