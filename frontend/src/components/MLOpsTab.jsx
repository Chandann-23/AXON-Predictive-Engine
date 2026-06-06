import React from 'react';

export default function MLOpsTab({
  inferenceLatency,
  apiOnline,
  modelMetadata,
  lastResult,
  mlopsStats,
  onForceRetrain
}) {
  const isRetraining = mlopsStats?.retraining_in_progress === true;
  const driftDetected = mlopsStats?.drift_detected === true;

  const getPValueColor = (pVal) => {
    if (pVal < 0.05) return '#ef4444'; // drifted
    if (pVal < 0.1) return '#f59e0b'; // warning
    return '#10b981'; // stable
  };

  return (
    <div className="fade-in">
      <h3 className="chart-title" style={{ marginBottom: '20px' }}>🛠️ MLOps Lifecycle Control & Infrastructure Status</h3>

      {/* Grid of basic parameters */}
      <div className="mlops-grid">
        {/* Inference Latency */}
        <div className="mlops-card">
          <div className="mlops-label">Inference Latency</div>
          <div className="mlops-value" style={{ color: '#00d4ff' }}>
            {inferenceLatency !== null && inferenceLatency !== undefined 
              ? `${inferenceLatency.toFixed(1)} ms`
              : '0.0 ms'}
          </div>
        </div>

        {/* API Status */}
        <div className="mlops-card">
          <div className="mlops-label">API Gateway Status</div>
          <div 
            className="mlops-value" 
            style={{ color: apiOnline ? '#10b981' : '#ef4444' }}
          >
            {apiOnline ? 'ONLINE' : 'OFFLINE'}
          </div>
        </div>

        {/* Model Meta */}
        <div className="mlops-card">
          <div className="mlops-label">Model Engine</div>
          <div className="mlops-value" style={{ fontSize: '1.1rem', padding: '6px 0', color: '#fff' }}>
            {modelMetadata.algorithm} ({modelMetadata.version})
          </div>
        </div>
      </div>

      {/* Drift Detection Warning Banner */}
      {driftDetected && (
        <div className="fade-in" style={{
          background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.18), rgba(239, 68, 68, 0.02))',
          border: '1px solid rgba(239, 68, 68, 0.35)',
          boxShadow: '0 0 15px rgba(239, 68, 68, 0.15)',
          padding: '16px 20px',
          borderRadius: '10px',
          color: '#ef4444',
          fontSize: '0.85rem',
          fontWeight: '700',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <span style={{ fontSize: '1.3rem' }}>🚨</span>
          <div>
            <div style={{ textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '2px' }}>Significant Data Drift Detected!</div>
            <div style={{ fontSize: '0.75rem', opacity: 0.85, fontWeight: '400' }}>
              The statistical distribution of live inputs differs significantly from the training baseline. Accuracy may degrade. Retraining is recommended.
            </div>
          </div>
        </div>
      )}

      <div className="mlops-columns-grid">
        {/* Left Column: Drift Detection Monitor */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="glass-card" style={{ margin: 0 }}>
            <h3 className="chart-title">📊 Statistical Data Drift Monitor</h3>
            <p style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.5)', lineHeight: '1.4', marginBottom: '15px' }}>
              Comparing live telemetry (last 30 pulses) against baseline training data (5,000 normal samples) using the <strong>Kolmogorov-Smirnov (K-S) two-sample test</strong>.
            </p>
            
            {mlopsStats?.drift_metrics && Object.keys(mlopsStats.drift_metrics).length > 0 ? (
              <div className="table-container" style={{ marginTop: 0 }}>
                <table className="history-table" style={{ fontSize: '0.8rem' }}>
                  <thead>
                    <tr>
                      <th>Metric</th>
                      <th>KS Statistic</th>
                      <th>p-value</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(mlopsStats.drift_metrics).map(([metricName, data]) => (
                      <tr key={metricName}>
                        <td style={{ fontWeight: '600', color: '#fff' }}>{metricName}</td>
                        <td>{data.ks_statistic.toFixed(4)}</td>
                        <td style={{ color: getPValueColor(data.p_value), fontWeight: '700' }}>
                          {data.p_value < 0.0001 ? '< 0.0001' : data.p_value.toFixed(4)}
                        </td>
                        <td>
                          <span className={`status-badge ${data.drifted ? 'badge-critical' : 'badge-stable'}`}>
                            {data.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '30px 10px', color: 'rgba(255,255,255,0.4)', fontSize: '0.8rem', background: 'rgba(0,0,0,0.15)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                {mlopsStats?.drift_message || 'Gathering telemetry database records...'}
              </div>
            )}
            
            <div style={{ marginTop: '15px', padding: '12px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.03)', fontSize: '0.72rem', color: 'rgba(255,255,255,0.45)', lineHeight: '1.4' }}>
              💡 <strong>Why p-value &lt; 0.05?</strong> In statistics, a p-value below 5% means we reject the hypothesis that the live telemetry follows the same distribution as the training data, indicating that the telemetry metrics have drifted.
            </div>
          </div>
        </div>

        {/* Right Column: Retraining Console & JSON Debugger */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="glass-card" style={{ margin: 0 }}>
            <h3 className="chart-title">🔄 Active Learning & Retraining Console</h3>
            <p style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.5)', lineHeight: '1.4', marginBottom: '20px' }}>
              Whenever operators report false positives, corrections are logged. Retraining automatically triggers every 5 feedback records, updating models seamlessly.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '20px' }}>
              <div style={{ padding: '15px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.03)', borderRadius: '8px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.4)', fontWeight: '600', textTransform: 'uppercase' }}>Operator Feedback</div>
                <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#00d4ff', marginTop: '5px' }}>
                  {mlopsStats ? mlopsStats.feedback_count : 0}
                </div>
                <div style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.3)', marginTop: '2px' }}>logged corrections</div>
              </div>
              <div style={{ padding: '15px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.03)', borderRadius: '8px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.4)', fontWeight: '600', textTransform: 'uppercase' }}>Retraining Trigger</div>
                <div style={{ fontSize: '1rem', fontWeight: '800', color: '#fff', marginTop: '15px' }}>
                  {mlopsStats && mlopsStats.feedback_count > 0 
                    ? `${5 - (mlopsStats.feedback_count % 5)} left`
                    : '5 left'}
                </div>
                <div style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.3)', marginTop: '2px' }}>until auto-retrain</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '12px 16px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.03)', borderRadius: '8px', fontSize: '0.8rem', color: '#fff', marginBottom: '20px' }}>
              <span className={`led-circle ${isRetraining ? 'led-orange' : 'led-green'}`}></span>
              <span>
                Retrainer State: <strong>{isRetraining ? 'Asynchronous Retraining Active' : 'Idle (Ready)'}</strong>
              </span>
            </div>

            <button 
              className={`btn-primary ${isRetraining ? 'btn-disabled' : ''}`}
              disabled={isRetraining}
              onClick={onForceRetrain}
            >
              {isRetraining ? (
                <>
                  <div className="loading-spinner" style={{ margin: '0 8px 0 0', width: '14px', height: '14px', border: '2px solid rgba(255,255,255,0.05)', borderTop: '2px solid #fff' }}></div>
                  Retraining ML Models...
                </>
              ) : (
                '🔄 Force Asynchronous Retrain'
              )}
            </button>
          </div>

          <div className="glass-card" style={{ margin: 0 }}>
            <h3 className="chart-title">🔍 MLOps Operations JSON Debugger</h3>
            {mlopsStats ? (
              <pre className="json-debugger-container" style={{ maxHeight: '200px' }}>
                {JSON.stringify(mlopsStats, null, 2)}
              </pre>
            ) : (
              <div style={{ padding: '20px', textAlign: 'center', color: 'rgba(255,255,255,0.4)', fontSize: '0.8rem' }}>
                Connecting to MLOps Stats API Gateway...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
