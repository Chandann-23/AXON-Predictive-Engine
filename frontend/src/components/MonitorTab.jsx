import React from 'react';

export default function MonitorTab({
  cpu, setCpu,
  ram, setRam,
  temp, setTemp,
  latency, setLatency,
  diskIo, setDiskIo,
  swapUsage, setSwapUsage,
  netThroughput, setNetThroughput,
  threadCount, setThreadCount,
  isLive, setIsLive,
  prediction,
  onReportFalsePositive,
  loading,
  error,
  prevCpu,
  prevRam,
  history,
  onExportCSV,
  applyPreset
}) {

  const formatTime = (tsStr) => {
    try {
      const date = new Date(tsStr);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return tsStr;
    }
  };

  const formatDate = (tsStr) => {
    try {
      const date = new Date(tsStr);
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    } catch {
      return '';
    }
  };

  const getStatusBadgeClass = (status) => {
    if (!status) return 'badge-stable';
    const s = status.toUpperCase();
    if (s === 'CRITICAL') return 'badge-critical';
    if (s === 'WARNING') return 'badge-warning';
    return 'badge-stable';
  };
  const getGaugeClass = (prob) => {
    if (prob >= 0.8) return 'gauge-critical';
    if (prob >= 0.5) return 'gauge-warning';
    return 'gauge-stable';
  };

  const getStatusText = (prob, status) => {
    if (!status) return 'STABLE';
    return status.toUpperCase();
  };

  const deltaCpu = (cpu - prevCpu).toFixed(1);
  const deltaRam = (ram - prevRam).toFixed(1);



  const getAdvisoryText = (prob, anomaly, status) => {
    if (anomaly) {
      return '🚨 Unsupervised anomaly detected! Telemetry patterns deviate from standard historical profiles. Verify subsystem workloads and inspect metrics for silent decay.';
    }
    if (prob >= 0.8) {
      return '🔴 Critical: Extreme failure probability. Subsystem overload is imminent. Workloads should be throttled immediately.';
    }
    if (prob >= 0.4) {
      return '🟡 Warning: Elevated failure probability. Monitor metrics closely. Run profile analysis to pinpoint resource bottlenecks.';
    }
    return '🟢 System is operating within normal baseline limits. Telemetry parameters are well balanced. No immediate action required.';
  };

  const getAdvisoryColor = (prob, anomaly) => {
    if (anomaly) return '#ef4444';
    if (prob >= 0.8) return '#ef4444';
    if (prob >= 0.4) return '#f59e0b';
    return 'rgba(255, 255, 255, 0.6)';
  };

  // Generate SVG path coordinates
  const renderSvgGraph = () => {
    if (!history || history.length < 2) return null;
    
    // Max 30 points to keep chart clean. Chronological left-to-right (reverse API desc order)
    const pointsData = [...history].slice(0, 30).reverse();
    
    const width = 800;
    const height = 200;
    const padding = { top: 20, right: 30, bottom: 30, left: 50 };
    
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    const xStep = chartWidth / (pointsData.length - 1);
    
    // Map points to SVG coordinates
    const coordinates = pointsData.map((d, index) => {
      const x = padding.left + index * xStep;
      const probVal = d.failure_probability > 1 ? d.failure_probability / 100 : d.failure_probability;
      const y = padding.top + chartHeight - (probVal * chartHeight);
      return { x, y, prob: probVal, ...d };
    });
    
    // Create Line Path
    let pathD = `M ${coordinates[0].x} ${coordinates[0].y}`;
    for (let i = 1; i < coordinates.length; i++) {
      pathD += ` L ${coordinates[i].x} ${coordinates[i].y}`;
    }
    
    // Create Fill Area Path (for gradient)
    const areaD = `${pathD} L ${coordinates[coordinates.length - 1].x} ${padding.top + chartHeight} L ${coordinates[0].x} ${padding.top + chartHeight} Z`;

    return (
      <svg viewBox={`0 0 ${width} ${height}`} className="history-svg">
        <defs>
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#00d4ff" stopOpacity="0.25"/>
            <stop offset="100%" stopColor="#00d4ff" stopOpacity="0.0"/>
          </linearGradient>
        </defs>
        
        {/* Horizontal Gridlines */}
        {[0, 0.25, 0.5, 0.75, 1.0].map((level, i) => {
          const yVal = padding.top + chartHeight - (level * chartHeight);
          return (
            <g key={i}>
              <line 
                x1={padding.left} 
                y1={yVal} 
                x2={width - padding.right} 
                y2={yVal} 
                stroke="rgba(255,255,255,0.05)" 
                strokeDasharray="4 4"
              />
              <text 
                x={padding.left - 10} 
                y={yVal + 4} 
                fill="rgba(255,255,255,0.4)" 
                fontSize="10" 
                textAnchor="end"
              >
                {(level * 100).toFixed(0)}%
              </text>
            </g>
          );
        })}
        
        {/* Area Gradient Fill */}
        <path d={areaD} fill="url(#areaGrad)" />
        
        {/* Stroke Line */}
        <path d={pathD} fill="none" stroke="#00d4ff" strokeWidth="2.5" strokeLinecap="round" />
        
        {/* Plot Nodes & Tooltips */}
        {coordinates.map((pt, i) => (
          <g key={i}>
            <circle 
              cx={pt.x} 
              cy={pt.y} 
              r="4" 
              fill="#080a0f" 
              stroke="#00d4ff" 
              strokeWidth="2"
            />
            {/* Show time on alternating steps or ends */}
            {(i === 0 || i === coordinates.length - 1 || i % 5 === 0) && (
              <text 
                x={pt.x} 
                y={height - 8} 
                fill="rgba(255,255,255,0.3)" 
                fontSize="9" 
                textAnchor="middle"
              >
                {formatTime(pt.timestamp)}
              </text>
            )}
          </g>
        ))}
      </svg>
    );
  };

  return (
    <div className="monitor-dashboard-clean fade-in">
      {/* Unsupervised Anomaly Warning Banner */}
      {prediction && prediction.anomaly_detected && (
        <div className="anomaly-warning-banner fade-in">
          <span style={{ fontSize: '1.2rem' }}>⚠️</span>
          <span>Unsupervised Anomaly Detected! (Outlier score: {prediction.anomaly_score ? prediction.anomaly_score.toFixed(4) : '0.0'})</span>
        </div>
      )}

      {/* Section 1: Interactive System Telemetry Nodes */}
      <div className="glass-card telemetry-nodes-container">
        <div className="telemetry-nodes-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.1rem' }}>📡</span>
            <h3 className="section-title">Interactive Telemetry Nodes & Control Panel</h3>
          </div>
          <div className="telemetry-nodes-actions">
            <span className="live-feed-label">AUTO-SIMULATE LIVE FEED</span>
            <label className="switch-toggle" style={{ transform: 'scale(0.85)', margin: 0 }}>
              <input 
                type="checkbox" 
                checked={isLive} 
                onChange={(e) => setIsLive(e.target.checked)} 
              />
              <span className="slider-toggle"></span>
            </label>
          </div>
        </div>

        <div className="telemetry-nodes-grid">
          {/* CPU Node */}
          <div className={`telemetry-node-card ${isLive ? 'live-pulsing' : ''}`}>
            <div className="node-header">
              <span className="node-label">CPU Usage</span>
              <span className="node-value" style={{ color: '#00d4ff' }}>{cpu.toFixed(1)}%</span>
            </div>
            <input 
              type="range" min="0" max="100" step="0.5" 
              value={cpu} onChange={(e) => setCpu(parseFloat(e.target.value))}
              disabled={isLive} className="slider-input"
            />
            <div className="node-footer">
              <span className={`mini-metric-delta ${parseFloat(deltaCpu) >= 0 ? 'delta-up' : 'delta-down'}`} style={{ fontSize: '0.68rem', fontWeight: '600' }}>
                {parseFloat(deltaCpu) >= 0 ? '▲' : '▼'} {Math.abs(deltaCpu)}% delta
              </span>
            </div>
          </div>

          {/* RAM Node */}
          <div className={`telemetry-node-card ${isLive ? 'live-pulsing' : ''}`}>
            <div className="node-header">
              <span className="node-label">RAM Usage</span>
              <span className="node-value" style={{ color: '#00d4ff' }}>{ram.toFixed(1)}%</span>
            </div>
            <input 
              type="range" min="0" max="100" step="0.5" 
              value={ram} onChange={(e) => setRam(parseFloat(e.target.value))}
              disabled={isLive} className="slider-input"
            />
            <div className="node-footer">
              <span className={`mini-metric-delta ${parseFloat(deltaRam) >= 0 ? 'delta-up' : 'delta-down'}`} style={{ fontSize: '0.68rem', fontWeight: '600' }}>
                {parseFloat(deltaRam) >= 0 ? '▲' : '▼'} {Math.abs(deltaRam)}% delta
              </span>
            </div>
          </div>

          {/* Temp Node */}
          <div className={`telemetry-node-card ${isLive ? 'live-pulsing' : ''}`}>
            <div className="node-header">
              <span className="node-label">Core Temp</span>
              <span className="node-value" style={{ color: '#00d4ff' }}>{temp.toFixed(1)}°C</span>
            </div>
            <input 
              type="range" min="0" max="120" step="0.5" 
              value={temp} onChange={(e) => setTemp(parseFloat(e.target.value))}
              disabled={isLive} className="slider-input"
            />

          </div>

          {/* Latency Node */}
          <div className={`telemetry-node-card ${isLive ? 'live-pulsing' : ''}`}>
            <div className="node-header">
              <span className="node-label">Net Latency</span>
              <span className="node-value" style={{ color: '#00d4ff' }}>{latency.toFixed(0)}ms</span>
            </div>
            <input 
              type="range" min="0" max="500" step="1" 
              value={latency} onChange={(e) => setLatency(parseFloat(e.target.value))}
              disabled={isLive} className="slider-input"
            />

          </div>

          {/* Disk I/O Node */}
          <div className={`telemetry-node-card ${isLive ? 'live-pulsing' : ''}`}>
            <div className="node-header">
              <span className="node-label">Disk I/O</span>
              <span className="node-value" style={{ color: '#00d4ff' }}>{diskIo.toFixed(1)}%</span>
            </div>
            <input 
              type="range" min="0" max="100" step="0.5" 
              value={diskIo} onChange={(e) => setDiskIo(parseFloat(e.target.value))}
              disabled={isLive} className="slider-input"
            />

          </div>

          {/* Swap Usage Node */}
          <div className={`telemetry-node-card ${isLive ? 'live-pulsing' : ''}`}>
            <div className="node-header">
              <span className="node-label">Swap Usage</span>
              <span className="node-value" style={{ color: '#00d4ff' }}>{swapUsage.toFixed(1)}%</span>
            </div>
            <input 
              type="range" min="0" max="100" step="0.5" 
              value={swapUsage} onChange={(e) => setSwapUsage(parseFloat(e.target.value))}
              disabled={isLive} className="slider-input"
            />

          </div>

          {/* Net Throughput Node */}
          <div className={`telemetry-node-card ${isLive ? 'live-pulsing' : ''}`}>
            <div className="node-header">
              <span className="node-label">Throughput</span>
              <span className="node-value" style={{ color: '#00d4ff' }}>{netThroughput.toFixed(0)} M</span>
            </div>
            <input 
              type="range" min="0" max="1000" step="5" 
              value={netThroughput} onChange={(e) => setNetThroughput(parseFloat(e.target.value))}
              disabled={isLive} className="slider-input"
            />

          </div>

          {/* Thread Count Node */}
          <div className={`telemetry-node-card ${isLive ? 'live-pulsing' : ''}`}>
            <div className="node-header">
              <span className="node-label">Active Threads</span>
              <span className="node-value" style={{ color: '#00d4ff' }}>{threadCount.toFixed(0)}</span>
            </div>
            <input 
              type="range" min="50" max="1000" step="10" 
              value={threadCount} onChange={(e) => setThreadCount(parseFloat(e.target.value))}
              disabled={isLive} className="slider-input"
            />

          </div>
        </div>
      </div>

      {/* Section 2: Health Gauge and Scenario/Metadata Grid */}
      <div className="dashboard-double-column">
        {/* Health Gauge Card */}
        <div className="glass-card health-gauge-card">
          <h3 className="chart-title">🛡️ AI System Health Gauge</h3>
          {loading && !prediction ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.8rem' }}>Syncing telemetry...</p>
            </div>
          ) : error ? (
            <div className="connection-error-container">
              <p style={{ fontWeight: '700', fontSize: '1rem', color: '#ef4444' }}>📡 Connection Failure</p>
              <p style={{ fontSize: '0.75rem', opacity: 0.8, marginTop: '8px' }}>
                Backend API server is offline. Ensure the Uvicorn server is running locally on port 10000.
              </p>
            </div>
          ) : prediction ? (
            <div className="health-gauge-inner" style={{ justifyContent: 'center' }}>
              <div className="gauge-display-wrapper">
                <div className={`gauge-card ${getGaugeClass(prediction.failure_probability)}`} style={{ padding: '24px' }}>
                  <div className="gauge-status" style={{ fontSize: '1.2rem' }}>{getStatusText(prediction.failure_probability, prediction.status)}</div>
                  <div className="gauge-value" style={{ fontSize: '4.2rem' }}>{(prediction.failure_probability * 100).toFixed(1)}%</div>
                  <div className="gauge-label">PROBABILITY OF FAILURE</div>
                </div>
                
                {prediction.status !== 'STABLE' && (
                  <button 
                    onClick={onReportFalsePositive}
                    className="btn-danger-outline"
                    style={{ marginTop: '12px' }}
                  >
                    🚫 Report False Positive
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="loading-container">Waiting for API signal...</div>
          )}
        </div>

        {/* Scenario Profiles and Engine Metadata Card */}
        <div className="glass-card scenario-metadata-card">
          <div className="scenario-section">
            <h3 className="chart-title" style={{ marginBottom: '12px' }}>🎛️ Scenario Profiles & Presets</h3>
            <div className="presets-grid-clean">
              <button className="preset-btn normal-preset" onClick={() => applyPreset('normal')}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span className="preset-icon">🟢</span>
                  <span style={{ fontWeight: '700' }}>Normal Load</span>
                </span>
              </button>
              <button className="preset-btn stress-preset" onClick={() => applyPreset('stress')}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span className="preset-icon">⚡</span>
                  <span style={{ fontWeight: '700' }}>CPU Stress</span>
                </span>
              </button>
              <button className="preset-btn spike-preset" onClick={() => applyPreset('network')}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span className="preset-icon">🌐</span>
                  <span style={{ fontWeight: '700' }}>Net Spike</span>
                </span>
              </button>
              <button className="preset-btn memory-preset" onClick={() => applyPreset('memory')}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span className="preset-icon">💾</span>
                  <span style={{ fontWeight: '700' }}>Memory Sat</span>
                </span>
              </button>
            </div>
          </div>
          
          <div className="metadata-section">
            <h4 className="metadata-title">🧠 Engine Metadata</h4>
            <div className="metadata-grid">
              <div className="insight-row">
                <span className="insight-label">Active Classifier</span>
                <span className="insight-val" style={{ color: '#00d4ff' }}>Random Forest</span>
              </div>
              <div className="insight-row">
                <span className="insight-label">Outlier Estimator</span>
                <span className="insight-val" style={{ color: '#ffb300' }}>Isolation Forest</span>
              </div>
              <div className="insight-row">
                <span className="insight-label">Baseline Sample</span>
                <span className="insight-val">5,000 Rows</span>
              </div>
              <div className="insight-row">
                <span className="insight-label">Drift Baseline</span>
                <span className="insight-val">K-S Test</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Section 3: Model Explainability Analytics Grid */}
      {prediction && (prediction.feature_importance || prediction.local_explainability) && (
        <div className="dashboard-double-column">
          {/* Feature Importance Card */}
          {prediction.feature_importance && (
            <div className="glass-card explainability-card">
              <h3 className="chart-title" style={{ marginBottom: '15px' }}>🔍 Dynamic Risk Drivers (AI Feature Importance)</h3>
              <div className="bar-chart-container">
                {Object.entries(prediction.feature_importance)
                  .sort((a, b) => b[1] - a[1])
                  .map(([feature, val]) => (
                    <div className="bar-row" key={feature} style={{ gridTemplateColumns: '80px 1fr 50px' }}>
                      <span className="bar-label">{feature}</span>
                      <div className="bar-wrapper">
                        <div 
                          className="bar-fill" 
                          style={{ width: `${val * 100}%` }}
                        ></div>
                      </div>
                      <span className="bar-value">{(val * 100).toFixed(1)}%</span>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Prediction Explainer (SHAP Local Contributions) */}
          {prediction.local_explainability && (
            <div className="glass-card explainability-card">
              <h3 className="chart-title" style={{ marginBottom: '15px' }}>📊 Prediction Explainer (SHAP Local Contributions)</h3>
              <div className="bar-chart-container">
                {Object.entries(prediction.local_explainability)
                  .sort((a, b) => b[1] - a[1])
                  .map(([feature, val]) => {
                    const percentage = val * 100;
                    const isPositive = val >= 0;
                    return (
                      <div className="bar-row" key={feature} style={{ gridTemplateColumns: '80px 1fr 60px' }}>
                        <span className="bar-label">{feature}</span>
                        <div className="bar-wrapper">
                          <div 
                            className="bar-fill" 
                            style={{ 
                              width: `${Math.min(100, Math.abs(percentage))}%`, 
                              background: isPositive 
                                ? 'linear-gradient(90deg, #ef4444, #f59e0b)' 
                                : 'linear-gradient(90deg, #10b981, #00d4ff)',
                              boxShadow: isPositive 
                                ? '0 0 8px rgba(239, 68, 68, 0.4)' 
                                : '0 0 8px rgba(0, 212, 255, 0.4)'
                            }}
                          ></div>
                        </div>
                        <span className="bar-value" style={{ color: isPositive ? '#ef4444' : '#00d4ff', fontWeight: '700' }}>
                          {isPositive ? '+' : ''}{percentage.toFixed(1)}%
                        </span>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* SVG Risk Trajectory Chart */}
      <div className="glass-card history-graph-card">
        <h3 className="chart-title">📈 Global Risk Trajectory (Last 30 Telemetry Pulses)</h3>
        {history && history.length >= 2 ? (
          <div className="svg-chart-container">
            {renderSvgGraph()}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '60px 0', color: 'rgba(255,255,255,0.4)', fontSize: '0.85rem' }}>
            Not enough data in database to render risk history curves. Trigger a few predictions!
          </div>
        )}
      </div>
    </div>
  );
}
