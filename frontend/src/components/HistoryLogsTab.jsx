import React from 'react';

export default function HistoryLogsTab({ history, onExportCSV }) {
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

  return (
    <div className="fade-in">
      <div className="sync-banner">
        <span>
          <div className="sync-dot"></div>
          AXON Database Sync Status: Connected (Full View)
        </span>
      </div>

      <div className="glass-card" style={{ width: '100%' }}>
        <h3 className="chart-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
          <span>🗄️ Core Database History Logs (Last 15 Entries)</span>
          {history && history.length > 0 && (
            <button onClick={onExportCSV} className="export-btn">
              📥 Export History (.CSV)
            </button>
          )}
        </h3>
        {history && history.length > 0 ? (
          <div className="table-container">
            <table className="history-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>CPU</th>
                  <th>RAM</th>
                  <th>Temp</th>
                  <th>Latency</th>
                  <th>Disk I/O</th>
                  <th>Swap</th>
                  <th>Net</th>
                  <th>Threads</th>
                  <th>Anomaly?</th>
                  <th>Risk</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {history.slice(0, 15).map((row, index) => {
                  const prob = row.failure_probability > 1 ? row.failure_probability / 100 : row.failure_probability;
                  const isAnomaly = row.anomaly_detected === true || row.anomaly_detected === 1;
                  return (
                    <tr key={row.id || index}>
                      <td>
                        <span style={{ color: '#fff', fontWeight: '500' }}>{formatTime(row.timestamp)}</span>
                        <span style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.3)', display: 'block' }}>{formatDate(row.timestamp)}</span>
                      </td>
                      <td>{row.cpu !== undefined ? row.cpu.toFixed(1) : (row.cpu_usage !== undefined ? row.cpu_usage.toFixed(1) : '0.0')}%</td>
                      <td>{row.ram !== undefined ? row.ram.toFixed(1) : (row.ram_usage !== undefined ? row.ram_usage.toFixed(1) : '0.0')}%</td>
                      <td>{row.temp !== undefined ? row.temp.toFixed(1) : (row.temp_celsius !== undefined ? row.temp_celsius.toFixed(1) : '0.0')}°C</td>
                      <td>{row.latency !== undefined ? row.latency.toFixed(0) : (row.network_latency !== undefined ? row.network_latency.toFixed(0) : '0')}ms</td>
                      <td>{row.disk_io !== undefined ? row.disk_io.toFixed(1) : '0.0'}%</td>
                      <td>{row.swap_usage !== undefined ? row.swap_usage.toFixed(1) : '0.0'}%</td>
                      <td>{row.net_throughput !== undefined ? row.net_throughput.toFixed(0) : '0'}M</td>
                      <td>{row.thread_count !== undefined ? row.thread_count.toFixed(0) : '0'}</td>
                      <td>
                        <span className={`status-badge ${isAnomaly ? 'badge-critical' : 'badge-stable'}`}>
                          {isAnomaly ? 'YES' : 'NO'}
                        </span>
                      </td>
                      <td style={{ color: '#00d4ff', fontWeight: '700' }}>{(prob * 100).toFixed(1)}%</td>
                      <td>
                        <span className={`status-badge ${getStatusBadgeClass(row.status)}`}>
                          {row.status ? row.status.toUpperCase() : 'STABLE'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'rgba(255,255,255,0.4)', fontSize: '0.85rem' }}>
            No history database logs found. Ensure you make predictions first.
          </div>
        )}
      </div>
    </div>
  );
}
