import React, { useState, useEffect, useRef } from 'react';
import MonitorTab from './components/MonitorTab';
import HistoryLogsTab from './components/HistoryLogsTab';
import MLOpsTab from './components/MLOpsTab';
import ValidationTab from './components/ValidationTab';

export default function App() {
  const [activeTab, setActiveTab] = useState('monitor');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  // Telemetry Inputs
  const [cpu, setCpu] = useState(50.0);
  const [ram, setRam] = useState(50.0);
  const [temp, setTemp] = useState(45.0);
  const [latency, setLatency] = useState(50.0);
  const [diskIo, setDiskIo] = useState(35.0);
  const [swapUsage, setSwapUsage] = useState(15.0);
  const [netThroughput, setNetThroughput] = useState(250.0);
  const [threadCount, setThreadCount] = useState(350.0);

  // For metric delta calculations
  const [prevCpu, setPrevCpu] = useState(50.0);
  const [prevRam, setPrevRam] = useState(50.0);

  // UI States
  const [isLive, setIsLive] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [inferenceLatency, setInferenceLatency] = useState(0.0);
  const [apiOnline, setApiOnline] = useState(false);
  const [lastResult, setLastResult] = useState(null);
  const [mlopsStats, setMlopsStats] = useState(null);

  // Reference to track previous values on updates
  const prevCpuRef = useRef(50.0);
  const prevRamRef = useRef(50.0);
  const telemetryRef = useRef({ cpu: 50.0, ram: 50.0, temp: 45.0, latency: 50.0, diskIo: 35.0, swapUsage: 15.0, netThroughput: 250.0, threadCount: 350.0 });

  // Model metadata details
  const modelMetadata = {
    version: 'v2.1.0',
    algorithm: 'RF + Isolation Forest (Hybrid)'
  };

  // Base API configuration (Reads VITE_API_URL or defaults to local backend)
  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:10000';

  // 1. Check API Health on Startup
  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_URL}/health`);
      if (res.ok) {
        setApiOnline(true);
      } else {
        setApiOnline(false);
      }
    } catch {
      setApiOnline(false);
    }
  };

  // 2. Fetch Telemetry History Logs
  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_URL}/history`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (err) {
      console.error('Failed to retrieve history logs:', err);
    }
  };

  // 3. Request Live AI Prediction
  const runPrediction = async (c, r, t, l, d, s, n, th) => {
    setLoading(true);
    setError(false);
    const startTime = performance.now();
    
    try {
      const queryParams = new URLSearchParams({
        cpu: c.toString(),
        ram: r.toString(),
        temp: t.toString(),
        latency: l.toString(),
        disk_io: d.toString(),
        swap_usage: s.toString(),
        net_throughput: n.toString(),
        thread_count: th.toString()
      });
      
      const res = await fetch(`${API_URL}/predict?${queryParams}`);
      const duration = performance.now() - startTime;
      setInferenceLatency(duration);

      if (res.ok) {
        const data = await res.json();
        setPrediction(data);
        setLastResult(data);
        setApiOnline(true);
        // Refresh history and MLOps metrics after logging new pulse
        fetchHistory();
        fetchMlopsStats();
      } else {
        setError(true);
        setPrediction(null);
      }
    } catch (err) {
      setError(true);
      setPrediction(null);
      setApiOnline(false);
      console.error('AI Inference Error:', err);
    } finally {
      setLoading(false);
    }
  };

  // 4. Report False Positive (Operator adjustment feedback loop)
  const handleReportFalsePositive = async () => {
    try {
      const res = await fetch(`${API_URL}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          cpu,
          ram,
          temp,
          latency,
          disk_io: diskIo,
          swap_usage: swapUsage,
          net_throughput: netThroughput,
          thread_count: threadCount,
          label: 'false_positive'
        })
      });
      if (res.ok) {
        alert('Operator adjustments logged. System will incorporate this on the next retraining loop.');
        fetchMlopsStats();
      } else {
        alert('Failed to register feedback in database.');
      }
    } catch (err) {
      console.error('Feedback recording failed:', err);
      alert('Network error writing feedback.');
    }
  };

  // 4b. Fetch MLOps Status / Drift metrics
  const fetchMlopsStats = async () => {
    try {
      const res = await fetch(`${API_URL}/mlops/stats`);
      if (res.ok) {
        const data = await res.json();
        setMlopsStats(data);
      }
    } catch (err) {
      console.error('Failed to retrieve MLOps stats:', err);
    }
  };

  // 4c. Force Manual Retraining
  const handleForceRetrain = async () => {
    try {
      const res = await fetch(`${API_URL}/mlops/retrain`, {
        method: 'POST'
      });
      if (res.ok) {
        alert('Asynchronous model retraining triggered successfully.');
        fetchMlopsStats();
      } else {
        const errData = await res.json();
        alert(`Failed to trigger retraining: ${errData.detail || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Error triggering retrain:', err);
      alert('Network error triggering model retrain.');
    }
  };

  // 5. Export History CSV
  const handleExportCSV = () => {
    if (!history || history.length === 0) return;
    
    const headers = [
      'ID', 'Timestamp', 'CPU (%)', 'RAM (%)', 'Temp (C)', 'Latency (ms)', 
      'Disk I/O (%)', 'Swap Usage (%)', 'Net Throughput (Mbps)', 'Thread Count',
      'Failure Probability', 'Status'
    ];
    const rows = history.map((h, i) => [
      h.id || i,
      h.timestamp,
      h.cpu !== undefined ? h.cpu : (h.cpu_usage || 0),
      h.ram !== undefined ? h.ram : (h.ram_usage || 0),
      h.temp !== undefined ? h.temp : (h.temp_celsius || 0),
      h.latency !== undefined ? h.latency : (h.network_latency || 0),
      h.disk_io !== undefined ? h.disk_io : 0,
      h.swap_usage !== undefined ? h.swap_usage : 0,
      h.net_throughput !== undefined ? h.net_throughput : 0,
      h.thread_count !== undefined ? h.thread_count : 0,
      h.failure_probability,
      h.status || 'STABLE'
    ]);

    const csvContent = [headers, ...rows]
      .map(e => e.map(val => `"${val}"`).join(','))
      .join('\n');
      
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `axon_history_${new Date().toISOString().slice(0,19).replace(/[:T]/g, '_')}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const applyPreset = (presetName) => {
    setIsLive(false);
    switch (presetName) {
      case 'normal':
        setCpu(35.0);
        setRam(42.5);
        setTemp(38.0);
        setLatency(15.0);
        setDiskIo(22.0);
        setSwapUsage(8.5);
        setNetThroughput(120.0);
        setThreadCount(180);
        break;
      case 'stress':
        setCpu(92.0);
        setRam(85.0);
        setTemp(95.0);
        setLatency(180.0);
        setDiskIo(45.0);
        setSwapUsage(15.0);
        setNetThroughput(250.0);
        setThreadCount(420);
        break;
      case 'network':
        setCpu(55.0);
        setRam(58.0);
        setTemp(48.0);
        setLatency(380.0);
        setDiskIo(25.0);
        setSwapUsage(12.0);
        setNetThroughput(950.0);
        setThreadCount(880);
        break;
      case 'memory':
        setCpu(75.5);
        setRam(94.0);
        setTemp(65.0);
        setLatency(85.0);
        setDiskIo(88.0);
        setSwapUsage(82.0);
        setNetThroughput(180.0);
        setThreadCount(350);
        break;
      default:
        break;
    }
  };

  // Run health check & fetch history / MLOps stats on mount
  useEffect(() => {
    checkHealth();
    fetchHistory();
    fetchMlopsStats();
    // Periodically sync health, logs, and drift metrics
    const interval = setInterval(() => {
      checkHealth();
      fetchHistory();
      fetchMlopsStats();
    }, 6000);
    return () => clearInterval(interval);
  }, []);

  // Update deltas and run predictions when manual sliders change (if not in live feed mode)
  useEffect(() => {
    if (isLive) return;
    
    const delayDebounce = setTimeout(() => {
      runPrediction(cpu, ram, temp, latency, diskIo, swapUsage, netThroughput, threadCount);
      
      // Update deltas
      setPrevCpu(prevCpuRef.current);
      setPrevRam(prevRamRef.current);
      
      prevCpuRef.current = cpu;
      prevRamRef.current = ram;
    }, 250); // Small debounce to avoid clogging API

    return () => clearTimeout(delayDebounce);
  }, [cpu, ram, temp, latency, diskIo, swapUsage, netThroughput, threadCount, isLive]);

  // Synchronize telemetryRef with current states
  useEffect(() => {
    telemetryRef.current = { cpu, ram, temp, latency, diskIo, swapUsage, netThroughput, threadCount };
  }, [cpu, ram, temp, latency, diskIo, swapUsage, netThroughput, threadCount]);

  // Live feed simulation logic
  useEffect(() => {
    if (!isLive) return;

    // Trigger immediate run
    const runLiveTick = () => {
      const current = telemetryRef.current;
      // Simulate random deviations relative to the current value
      const nextCpu = Math.min(100, Math.max(0, current.cpu + (Math.random() - 0.5) * 15));
      const nextRam = Math.min(100, Math.max(0, current.ram + (Math.random() - 0.5) * 10));
      const nextTemp = Math.min(120, Math.max(20, current.temp + (Math.random() - 0.5) * 8));
      const nextLatency = Math.min(500, Math.max(5, current.latency + (Math.random() - 0.5) * 40));
      const nextDiskIo = Math.min(100, Math.max(0, current.diskIo + (Math.random() - 0.5) * 15));
      const nextSwapUsage = Math.min(100, Math.max(0, current.swapUsage + (Math.random() - 0.5) * 8));
      const nextNetThroughput = Math.min(1000, Math.max(0, current.netThroughput + (Math.random() - 0.5) * 100));
      const nextThreadCount = Math.min(1000, Math.max(50, current.threadCount + (Math.random() - 0.5) * 80));

      setCpu(nextCpu);
      setRam(nextRam);
      setTemp(nextTemp);
      setLatency(nextLatency);
      setDiskIo(nextDiskIo);
      setSwapUsage(nextSwapUsage);
      setNetThroughput(nextNetThroughput);
      setThreadCount(nextThreadCount);

      runPrediction(nextCpu, nextRam, nextTemp, nextLatency, nextDiskIo, nextSwapUsage, nextNetThroughput, nextThreadCount);
      
      setPrevCpu(prevCpuRef.current);
      setPrevRam(prevRamRef.current);
      prevCpuRef.current = nextCpu;
      prevRamRef.current = nextRam;
    };

    runLiveTick();

    const interval = setInterval(runLiveTick, 2500); // Pulse every 2.5s
    return () => clearInterval(interval);
  }, [isLive]);

  const getPageTitle = () => {
    switch (activeTab) {
      case 'monitor':
        return '📡 Real-Time Telemetry Monitor';
      case 'history':
        return '🗄️ Core Database History Logs';
      case 'mlops':
        return '⚙️ MLOps Lifecycle & Drift Monitor';
      case 'validation':
        return '🛡️ Automated System Validation Playbook';
      default:
        return 'AXON Predictive Engine';
    }
  };

  const getPageSubtitle = () => {
    switch (activeTab) {
      case 'monitor':
        return 'Monitor live resource load metrics and explain predictions using SHAP contributions.';
      case 'history':
        return 'Review system telemetry database rows (limited to the last 15 entries).';
      case 'mlops':
        return 'Analyze statistical Kolmogorov-Smirnov drift metrics and trigger active learning retrains.';
      case 'validation':
        return 'Execute automated test runs to audit the integrity, explainability, and quality pipelines.';
      default:
        return '';
    }
  };

  return (
    <div className={`app-container ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      {/* Sidebar Navigation */}
      <nav className={`sidebar-nav ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-top">
          <div className="nav-logo-text" style={{ textShadow: '0 0 10px rgba(0, 212, 255, 0.3)', marginBottom: '10px' }}>
            AXON ENGINE
          </div>
          
          <div className="nav-links-vertical">
            <button 
              className={`nav-tab-btn-vertical ${activeTab === 'monitor' ? 'active' : ''}`}
              onClick={() => setActiveTab('monitor')}
            >
              <span className="nav-icon">📊</span>
              <span>01 / Monitor</span>
            </button>
            <button 
              className={`nav-tab-btn-vertical ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => setActiveTab('history')}
            >
              <span className="nav-icon">🗄️</span>
              <span>02 / History Logs</span>
            </button>
            <button 
              className={`nav-tab-btn-vertical ${activeTab === 'mlops' ? 'active' : ''}`}
              onClick={() => setActiveTab('mlops')}
            >
              <span className="nav-icon">⚙️</span>
              <span>03 / MLOps Lifecycle</span>
            </button>
            <button 
              className={`nav-tab-btn-vertical ${activeTab === 'validation' ? 'active' : ''}`}
              onClick={() => setActiveTab('validation')}
            >
              <span className="nav-icon">🛡️</span>
              <span>04 / System Validation</span>
            </button>
          </div>
        </div>

        <div className="sidebar-footer">
          <div className="sidebar-status">
            <span className={`led-circle ${apiOnline ? 'led-green' : 'led-red'}`} style={{ width: '8px', height: '8px' }}></span>
            <span className="led-text" style={{ fontSize: '0.65rem', letterSpacing: '0.5px' }}>API GATEWAY: {apiOnline ? 'ONLINE' : 'OFFLINE'}</span>
          </div>
          <div className="sidebar-version">v2.1.0</div>
        </div>
      </nav>

      {/* Main Content Area */}
      <div className="main-content-wrapper">
        <main className="main-content">
          {/* Dynamic Page Header */}
          <div className="page-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <button 
                className="sidebar-toggle-btn" 
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                title={sidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
              >
                {sidebarCollapsed ? '☰' : '◀'}
              </button>
              <div>
                <h2 className="page-title-text">{getPageTitle()}</h2>
                <div className="page-subtitle-text">{getPageSubtitle()}</div>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className={`led-circle ${apiOnline ? 'led-green' : 'led-red'}`} style={{ width: '8px', height: '8px' }}></span>
              <span style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.4)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                SYSTEM STATUS: {apiOnline ? 'OPERATIONAL' : 'OFFLINE'}
              </span>
            </div>
          </div>

          {/* Body tabs container */}
          {activeTab === 'monitor' && (
            <MonitorTab 
              cpu={cpu} setCpu={setCpu}
              ram={ram} setRam={setRam}
              temp={temp} setTemp={setTemp}
              latency={latency} setLatency={setLatency}
              diskIo={diskIo} setDiskIo={setDiskIo}
              swapUsage={swapUsage} setSwapUsage={setSwapUsage}
              netThroughput={netThroughput} setNetThroughput={setNetThroughput}
              threadCount={threadCount} setThreadCount={setThreadCount}
              isLive={isLive} setIsLive={setIsLive}
              prediction={prediction}
              onReportFalsePositive={handleReportFalsePositive}
              loading={loading}
              error={error}
              prevCpu={prevCpu}
              prevRam={prevRam}
              history={history}
              onExportCSV={handleExportCSV}
              applyPreset={applyPreset}
            />
          )}

          {activeTab === 'history' && (
            <HistoryLogsTab 
              history={history}
              onExportCSV={handleExportCSV}
            />
          )}

          {activeTab === 'mlops' && (
            <MLOpsTab 
              inferenceLatency={inferenceLatency}
              apiOnline={apiOnline}
              modelMetadata={modelMetadata}
              lastResult={lastResult}
              mlopsStats={mlopsStats}
              onForceRetrain={handleForceRetrain}
            />
          )}

          {activeTab === 'validation' && (
            <ValidationTab 
              applyPreset={applyPreset}
              setActiveTab={setActiveTab}
              mlopsStats={mlopsStats}
              onForceRetrain={handleForceRetrain}
            />
          )}
        </main>
      </div>
    </div>
  );
}
