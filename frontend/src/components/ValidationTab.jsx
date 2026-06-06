import React from 'react';

export default function ValidationTab({ applyPreset, setActiveTab, mlopsStats, onForceRetrain }) {
  const testCases = [
    {
      id: 'TEST-01',
      name: 'Baseline System Integrity Verification',
      subsystem: 'Supervised Inference Engine',
      focus: 'Prediction Probability',
      preset: 'normal',
      targetTab: 'monitor',
      description: 'Verifies that the predictive models yield a low, stable failure risk under safe baseline system inputs. Highlights stabilizing SHAP contributors.',
      expected: 'Risk < 5.0%, health gauge status "STABLE", negative SHAP contributions on CPU, RAM, and Latency.',
      actionLabel: 'Run Baseline Verification'
    },
    {
      id: 'TEST-02',
      name: 'Additive Attribution Explainability (SHAP)',
      subsystem: 'Model Transparency Engine',
      focus: 'SHAP Feature Contribution Weights',
      preset: 'stress',
      targetTab: 'monitor',
      description: 'Verifies the local explainability engine by overloading the CPU and temperature. Asserts that temp and CPU are identified as the primary drivers of the elevated risk.',
      expected: 'Risk > 90.0%, health gauge status "CRITICAL", temp and CPU identified as the highest positive contributors.',
      actionLabel: 'Run Explainability Test'
    },
    {
      id: 'TEST-03',
      name: 'Covariate Shift Detection (K-S Data Drift)',
      subsystem: 'Data Quality & Drift Pipeline',
      focus: 'Kolmogorov-Smirnov two-sample p-value',
      preset: 'network',
      targetTab: 'mlops',
      description: 'Verifies that the MLOps statistical monitoring pipeline detects covariate drift when telemetry variables shift outside baseline training parameters (5,000 normal logs).',
      expected: 'Drift status rejects null hypothesis (p-value < 0.05) and flags shifted features (e.g. Net, Threads) as "DRIFTED".',
      actionLabel: 'Run Drift Analysis'
    },
    {
      id: 'TEST-04',
      name: 'Closed-Loop Active Learning Retraining',
      subsystem: 'Zero-Downtime Retraining Controller',
      focus: 'Feedback Counting & Memory Hotswapping',
      preset: 'memory',
      targetTab: 'mlops',
      description: 'Verifies the active learning pipeline. Simulates operator feedback loops by force retraining the models asynchronously in a daemon thread, hot-swapping memory references.',
      expected: 'Background thread reloads models in memory upon successful retraining without prediction service interruption.',
      actionLabel: 'Run Retraining Loop'
    }
  ];

  const handleRunTest = (tc) => {
    if (tc.preset === 'memory') {
      if (onForceRetrain) onForceRetrain();
      setActiveTab(tc.targetTab);
    } else {
      applyPreset(tc.preset);
      setActiveTab(tc.targetTab);
    }
  };

  return (
    <div className="fade-in">
      <div className="sync-banner" style={{ background: 'linear-gradient(90deg, rgba(0,212,255,0.1), transparent)' }}>
        <span>
          <div className="sync-dot" style={{ backgroundColor: '#10b981', boxShadow: '0 0 8px #10b981' }}></div>
          AXON Engine Verification Suite: Active (ProductionQA Mode)
        </span>
      </div>

      <div className="glass-card" style={{ width: '100%', padding: '22px' }}>
        <h3 className="chart-title" style={{ fontSize: '1.1rem', marginBottom: '20px' }}>
          🛡️ AXON ML Engine — System Verification & Validation Playbook
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {testCases.map((tc) => (
            <div
              key={tc.id}
              className="glass-card"
              style={{
                margin: 0,
                padding: '18px',
                background: 'rgba(255,255,255,0.01)',
                border: '1px solid rgba(255,255,255,0.06)',
                borderRadius: '10px',
                display: 'flex',
                flexDirection: 'column',
                gap: '14px'
              }}
            >
              {/* Card Header */}
              <div
                className="validation-card-header"
                style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                  <span style={{
                    fontSize: '0.62rem', fontWeight: '800',
                    background: 'rgba(0,212,255,0.15)', color: '#00d4ff',
                    padding: '3px 8px', borderRadius: '4px', letterSpacing: '1px',
                    flexShrink: 0
                  }}>
                    {tc.id}
                  </span>
                  <h4 style={{ fontSize: '0.88rem', fontWeight: '700', color: '#fff', margin: 0 }}>
                    {tc.name}
                  </h4>
                </div>
                <span className="status-badge badge-stable" style={{ backgroundColor: 'rgba(16,185,129,0.1)', color: '#10b981', border: '1px solid rgba(16,185,129,0.2)', flexShrink: 0 }}>
                  READY
                </span>
              </div>

              {/* Technical Specs */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                gap: '10px',
                fontSize: '0.72rem',
                background: 'rgba(0,0,0,0.15)',
                padding: '11px',
                borderRadius: '6px'
              }}>
                <div>
                  <span style={{ color: 'rgba(255,255,255,0.38)', display: 'block', marginBottom: '2px' }}>QA Subsystem</span>
                  <strong style={{ color: '#fff' }}>{tc.subsystem}</strong>
                </div>
                <div>
                  <span style={{ color: 'rgba(255,255,255,0.38)', display: 'block', marginBottom: '2px' }}>Focus Metric</span>
                  <strong style={{ color: '#00d4ff' }}>{tc.focus}</strong>
                </div>
                <div>
                  <span style={{ color: 'rgba(255,255,255,0.38)', display: 'block', marginBottom: '2px' }}>Test Type</span>
                  <strong style={{ color: '#fff' }}>{tc.preset === 'memory' ? 'Automated Job' : 'Interactive Preset'}</strong>
                </div>
              </div>

              {/* Description */}
              <div style={{ fontSize: '0.76rem', lineHeight: '1.45', color: 'rgba(255,255,255,0.62)' }}>
                <span style={{ color: 'rgba(255,255,255,0.38)', fontWeight: '600', display: 'block', marginBottom: '3px', fontSize: '0.66rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Test Description
                </span>
                {tc.description}
              </div>

              {/* Expected Outcomes */}
              <div style={{ fontSize: '0.76rem', lineHeight: '1.45', color: 'rgba(255,255,255,0.62)', borderLeft: '3px solid #00d4ff', paddingLeft: '12px' }}>
                <span style={{ color: 'rgba(255,255,255,0.38)', fontWeight: '600', display: 'block', marginBottom: '2px', fontSize: '0.66rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Expected QA Verification
                </span>
                {tc.expected}
              </div>

              {/* Run Button */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '4px' }}>
                <button
                  onClick={() => handleRunTest(tc)}
                  className="btn-primary validation-run-btn"
                  style={{ width: 'auto', padding: '10px 18px', fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '7px' }}
                >
                  🚀 {tc.actionLabel}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
