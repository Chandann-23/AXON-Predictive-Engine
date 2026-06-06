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

  // Reference to track previous values
  const prevCpuRef = useRef(50.0);
  const prevRamRef = useRef(50.0);
  const telemetryRef = useRef({ cpu: 50.0, ram: 50.0, temp: 45.0, latency: 50.0, diskIo: 35.0, swapUsage: 15.0, netThroughput: 250.0, threadCount: 350.0 });

  const modelMetadata = {
    version: 'v2.1.0',
    algorithm: 'RF + Isolation Forest (Hybrid)'
  };

  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:10000';

  // 1. Health Check
  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_URL}/health`);
      setApiOnline(res.ok);
    } catch {
      setApiOnline(false);
    }
  };

  // 2. Fetch History
  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_URL}/history?_t=${Date.now()}`);
      if (res.ok) setHistory(await res.json());
    } catch (err) {
      console.error('Failed to retrieve history:', err);
    }
  };

  // 3. Run Prediction
  const runPrediction = async (c, r, t, l, d, s, n, th) => {
    setLoading(true);
    setError(false);
    const startTime = performance.now();
    try {
      const queryParams = new URLSearchParams({
        cpu: c.toString(), ram: r.toString(), temp: t.toString(),
        latency: l.toString(), disk_io: d.toString(), swap_usage: s.toString(),
        net_throughput: n.toString(), thread_count: th.toString(),
        _t: Date.now().toString()
      });
      const res = await fetch(`${API_URL}/predict?${queryParams}`);
      const duration = performance.now() - startTime;
      setInferenceLatency(duration);
      if (res.ok) {
        const data = await res.json();
        setPrediction(data);
        setLastResult(data);
        setApiOnline(true);
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

  // 4. Report False Positive
  const handleReportFalsePositive = async () => {
    try {
      const res = await fetch(`${API_URL}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cpu, ram, temp, latency, disk_io: diskIo, swap_usage: swapUsage, net_throughput: netThroughput, thread_count: threadCount, label: 'false_positive' })
      });
      if (res.ok) {
        alert('Operator adjustments logged. System will incorporate this on the next retraining loop.');
        fetchMlopsStats();
      } else {
        alert('Failed to register feedback in database.');
      }
    } catch (err) {
      console.error('Feedback error:', err);
      alert('Network error writing feedback.');
    }
  };

  // 4b. Fetch MLOps Stats
  const fetchMlopsStats = async () => {
    try {
      const res = await fetch(`${API_URL}/mlops/stats?_t=${Date.now()}`);
      if (res.ok) setMlopsStats(await res.json());
    } catch (err) {
      console.error('Failed to retrieve MLOps stats:', err);
    }
  };

  // 4c. Force Retrain
  const handleForceRetrain = async () => {
    try {
      const res = await fetch(`${API_URL}/mlops/retrain`, { method: 'POST' });
      if (res.ok) {
        alert('Asynchronous model retraining triggered successfully.');
        fetchMlopsStats();
      } else {
        const errData = await res.json();
        alert(`Failed to trigger retraining: ${errData.detail || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Retrain error:', err);
      alert('Network error triggering model retrain.');
    }
  };

  // 5. Export CSV
  const handleExportCSV = () => {
    if (!history || history.length === 0) return;
    const headers = ['ID','Timestamp','CPU (%)','RAM (%)','Temp (C)','Latency (ms)','Disk I/O (%)','Swap Usage (%)','Net Throughput (Mbps)','Thread Count','Failure Probability','Status'];
    const rows = history.map((h, i) => [
      h.id || i, h.timestamp,
      h.cpu !== undefined ? h.cpu : (h.cpu_usage || 0),
      h.ram !== undefined ? h.ram : (h.ram_usage || 0),
      h.temp !== undefined ? h.temp : (h.temp_celsius || 0),
      h.latency !== undefined ? h.latency : (h.network_latency || 0),
      h.disk_io !== undefined ? h.disk_io : 0,
      h.swap_usage !== undefined ? h.swap_usage : 0,
      h.net_throughput !== undefined ? h.net_throughput : 0,
      h.thread_count !== undefined ? h.thread_count : 0,
      h.failure_probability, h.status || 'STABLE'
    ]);
    const csvContent = [headers, ...rows].map(e => e.map(val => `"${val}"`).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `axon_history_${new Date().toISOString().slice(0,19).replace(/[:T]/g,'_')}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const applyPreset = (presetName) => {
    setIsLive(false);
    switch (presetName) {
      case 'normal':  setCpu(35.0); setRam(42.5); setTemp(38.0); setLatency(15.0); setDiskIo(22.0); setSwapUsage(8.5);  setNetThroughput(120.0); setThreadCount(180); break;
      case 'stress':  setCpu(92.0); setRam(85.0); setTemp(95.0); setLatency(180.0); setDiskIo(45.0); setSwapUsage(15.0); setNetThroughput(250.0); setThreadCount(420); break;
      case 'network': setCpu(55.0); setRam(58.0); setTemp(48.0); setLatency(380.0); setDiskIo(25.0); setSwapUsage(12.0); setNetThroughput(950.0); setThreadCount(880); break;
      case 'memory':  setCpu(75.5); setRam(94.0); setTemp(65.0); setLatency(85.0); setDiskIo(88.0); setSwapUsage(82.0); setNetThroughput(180.0); setThreadCount(350); break;
      default: break;
    }
  };

  useEffect(() => {
    checkHealth();
    fetchHistory();
    fetchMlopsStats();
    const interval = setInterval(() => { checkHealth(); fetchHistory(); fetchMlopsStats(); }, 6000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (isLive) return;
    const delay = setTimeout(() => {
      runPrediction(cpu, ram, temp, latency, diskIo, swapUsage, netThroughput, threadCount);
      setPrevCpu(prevCpuRef.current);
      setPrevRam(prevRamRef.current);
      prevCpuRef.current = cpu;
      prevRamRef.current = ram;
    }, 250);
    return () => clearTimeout(delay);
  }, [cpu, ram, temp, latency, diskIo, swapUsage, netThroughput, threadCount, isLive]);

  useEffect(() => {
    telemetryRef.current = { cpu, ram, temp, latency, diskIo, swapUsage, netThroughput, threadCount };
  }, [cpu, ram, temp, latency, diskIo, swapUsage, netThroughput, threadCount]);

  useEffect(() => {
    if (!isLive) return;
    const runLiveTick = () => {
      const cur = telemetryRef.current;
      const nextCpu  = Math.min(100, Math.max(0, cur.cpu + (Math.random() - 0.5) * 15));
      const nextRam  = Math.min(100, Math.max(0, cur.ram + (Math.random() - 0.5) * 10));
      const nextTemp = Math.min(120, Math.max(20, cur.temp + (Math.random() - 0.5) * 8));
      const nextLat  = Math.min(500, Math.max(5, cur.latency + (Math.random() - 0.5) * 40));
      const nextDisk = Math.min(100, Math.max(0, cur.diskIo + (Math.random() - 0.5) * 15));
      const nextSwap = Math.min(100, Math.max(0, cur.swapUsage + (Math.random() - 0.5) * 8));
      const nextNet  = Math.min(1000, Math.max(0, cur.netThroughput + (Math.random() - 0.5) * 100));
      const nextThr  = Math.min(1000, Math.max(50, cur.threadCount + (Math.random() - 0.5) * 80));
      setCpu(nextCpu); setRam(nextRam); setTemp(nextTemp); setLatency(nextLat);
      setDiskIo(nextDisk); setSwapUsage(nextSwap); setNetThroughput(nextNet); setThreadCount(nextThr);
      runPrediction(nextCpu, nextRam, nextTemp, nextLat, nextDisk, nextSwap, nextNet, nextThr);
      setPrevCpu(prevCpuRef.current);
      setPrevRam(prevRamRef.current);
      prevCpuRef.current = nextCpu;
      prevRamRef.current = nextRam;
    };
    runLiveTick();
    const interval = setInterval(runLiveTick, 2500);
    return () => clearInterval(interval);
  }, [isLive]);

  // Navigation config
  const tabs = [
    { id: 'monitor',    icon: '📊', label: 'Monitor',    shortTitle: '📡 Monitor',          fullTitle: '📡 Real-Time Telemetry Monitor',         subtitle: '' },
    { id: 'history',   icon: '🗄️', label: 'History',    shortTitle: '🗄️ History Logs',     fullTitle: '🗄️ Core Database History Logs',           subtitle: '' },
    { id: 'mlops',     icon: '⚙️', label: 'MLOps',      shortTitle: '⚙️ MLOps',            fullTitle: '⚙️ MLOps Lifecycle & Drift Monitor',       subtitle: '' },
    { id: 'validation',icon: '🛡️', label: 'Validate',   shortTitle: '🛡️ Validation',       fullTitle: '🛡️ Automated System Validation Playbook', subtitle: '' },
  ];

  const activeTabConfig = tabs.find(t => t.id === activeTab) || tabs[0];

  return (
    <div className={`app-container ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>

      {/* ═══ Desktop Sidebar Navigation ═══════════════════════ */}
      <nav className={`sidebar-nav ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-top">
          <div className="nav-logo-text">AXON ENGINE</div>

          <div className="nav-links-vertical">
            {tabs.map(tab => (
              <button
                key={tab.id}
                className={`nav-tab-btn-vertical ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <span className="nav-icon">{tab.icon}</span>
                <span>{tab.label === 'Monitor' ? '01 / Monitor' : tab.label === 'History' ? '02 / History Logs' : tab.label === 'MLOps' ? '03 / MLOps Lifecycle' : '04 / System Validation'}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="sidebar-footer">
          <div className="sidebar-status">
            <span className={`led-circle ${apiOnline ? 'led-green' : 'led-red'}`} style={{ width: '8px', height: '8px' }}></span>
            <span className="led-text" style={{ fontSize: '0.62rem', letterSpacing: '0.5px' }}>
              API: {apiOnline ? 'ONLINE' : 'OFFLINE'}
            </span>
          </div>
          <div className="sidebar-version">v2.1.0</div>
        </div>
      </nav>

      {/* ═══ Main Content ════════════════════════════════════ */}
      <div className="main-content-wrapper">

        {/* Mobile Header Bar (logo + status LED) */}
        <div className="mobile-header-bar">
          <span className="mobile-header-logo">AXON</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span className={`led-circle ${apiOnline ? 'led-green' : 'led-red'}`} style={{ width: '7px', height: '7px' }}></span>
            <span style={{ fontSize: '0.62rem', color: 'rgba(255,255,255,0.5)', fontWeight: '700', textTransform: 'uppercase' }}>
              {apiOnline ? 'ONLINE' : 'OFFLINE'}
            </span>
          </div>
        </div>

        <main className="main-content">
          {/* Desktop Page Header */}
          <div className="page-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <button
                className="sidebar-toggle-btn"
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                title={sidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
              >
                {sidebarCollapsed ? '☰' : '◀'}
              </button>
              <div>
                <h2 className="page-title-text">{activeTabConfig.fullTitle}</h2>
                {activeTabConfig.subtitle && <div className="page-subtitle-text">{activeTabConfig.subtitle}</div>}
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
              <span className={`led-circle ${apiOnline ? 'led-green' : 'led-red'}`} style={{ width: '8px', height: '8px' }}></span>
              <span className="header-status-text" style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.4)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                SYSTEM: {apiOnline ? 'OPERATIONAL' : 'OFFLINE'}
              </span>
            </div>
          </div>

          {/* Tab Content */}
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

      {/* ═══ Mobile Bottom Tab Bar (≤768px only) ════════════ */}
      <nav className="mobile-bottom-nav" role="navigation" aria-label="Mobile navigation">
        <div className="mobile-bottom-nav-inner">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`mobile-nav-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
              aria-label={tab.label}
            >
              <span className="mobile-nav-icon">{tab.icon}</span>
              <span className="mobile-nav-label">{tab.label}</span>
            </button>
          ))}
        </div>
      </nav>

    </div>
  );
}
