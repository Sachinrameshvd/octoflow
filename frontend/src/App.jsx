import React, { useState, useEffect } from 'react';

const ARM_ROLES = [
  { id: 0, title: 'System Architect', color: '#00F0FF', domain: 'Topology & Interfaces' },
  { id: 1, title: 'Database Engineer', color: '#39FF14', domain: 'Schemas & Migrations' },
  { id: 2, title: 'Backend API Developer', color: '#00E5FF', domain: 'FastAPI / REST' },
  { id: 3, title: 'Frontend UI Engineer', color: '#BF55EC', domain: 'Views & Components' },
  { id: 4, title: 'State & Optimization', color: '#FFB900', domain: 'Reactivity & Latency' },
  { id: 5, title: 'Integration QA Tester', color: '#00FF66', domain: 'Pytest & Contracts' },
  { id: 6, title: 'Security & Profiling', color: '#FF0055', domain: 'PII & Vulnerabilities' },
  { id: 7, title: 'DevOps & Deployment', color: '#0099FF', domain: 'Docker & CI Pipelines' },
];

export default function App() {
  const [telemetry, setTelemetry] = useState({
    activeArmCount: 8,
    quiescentArms: 8,
    savingsPct: 87.5,
    totalCost: 0.042,
    cycle: 1,
    maxCycles: 10,
    status: 'GLOBAL_QUIESCENCE',
    arms: ARM_ROLES.map((role) => ({
      ...role,
      surprise: 0.04 + Math.random() * 0.05,
      threshold: 0.45,
      silentSteps: 12 + Math.floor(Math.random() * 5),
      escalations: 0,
      status: 'SILENT_EXECUTION',
    })),
  });

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0a0d14',
      color: '#e2e8f0',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      padding: '24px 32px',
    }}>
      {/* Header */}
      <header style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: '1px solid #1e293b',
        paddingBottom: '20px',
        marginBottom: '28px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #00f0ff 0%, #bf55ec 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 'bold',
            fontSize: '22px',
            color: '#0a0d14',
          }}>
            🐙
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 700, letterSpacing: '-0.5px' }}>
              OctoFlow Swarm Cockpit
            </h1>
            <p style={{ margin: '2px 0 0 0', fontSize: '13px', color: '#94a3b8' }}>
              Biologically-Inspired Cephalopod Multi-Agent Intelligence
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 14px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: 600,
            backgroundColor: 'rgba(57, 255, 20, 0.1)',
            color: '#39ff14',
            border: '1px solid rgba(57, 255, 20, 0.3)',
          }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#39ff14' }} />
            {telemetry.status}
          </span>
        </div>
      </header>

      {/* Top Stat Gauges */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px',
        marginBottom: '28px',
      }}>
        <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '16px' }}>
          <div style={{ fontSize: '12px', color: '#9ca3af', textTransform: 'uppercase' }}>Token Savings</div>
          <div style={{ fontSize: '28px', fontWeight: 700, color: '#00f0ff', marginTop: '4px' }}>
            {telemetry.savingsPct}%
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>Silent sensory predictive coding</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '16px' }}>
          <div style={{ fontSize: '12px', color: '#9ca3af', textTransform: 'uppercase' }}>Ganglia Quiescence</div>
          <div style={{ fontSize: '28px', fontWeight: 700, color: '#39ff14', marginTop: '4px' }}>
            {telemetry.quiescentArms} / 8 Arms
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>Convergence verification verified</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '16px' }}>
          <div style={{ fontSize: '12px', color: '#9ca3af', textTransform: 'uppercase' }}>Swarm Cost</div>
          <div style={{ fontSize: '28px', fontWeight: 700, color: '#bf55ec', marginTop: '4px' }}>
            ${telemetry.totalCost.toFixed(3)}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>Cognitive tier optimization</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '16px' }}>
          <div style={{ fontSize: '12px', color: '#9ca3af', textTransform: 'uppercase' }}>Convergence Cycle</div>
          <div style={{ fontSize: '28px', fontWeight: 700, color: '#f59e0b', marginTop: '4px' }}>
            Cycle {telemetry.cycle} / {telemetry.maxCycles}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>Supraesophageal Conductor</div>
        </div>
      </div>

      {/* 8 Ganglia Arms Grid */}
      <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px' }}>8-Arm Ganglia Nervous Ring</h2>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '16px',
      }}>
        {telemetry.arms.map((arm) => (
          <div key={arm.id} style={{
            background: '#111827',
            border: `1px solid ${arm.surprise > arm.threshold ? '#ef4444' : '#1f2937'}`,
            borderRadius: '12px',
            padding: '16px',
            position: 'relative',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  backgroundColor: arm.color,
                  boxShadow: `0 0 8px ${arm.color}`,
                }} />
                <span style={{ fontWeight: 600, fontSize: '14px' }}>Arm {arm.id}: {arm.title}</span>
              </div>
              <span style={{ fontSize: '11px', color: '#9ca3af', backgroundColor: '#1e293b', padding: '2px 8px', borderRadius: '6px' }}>
                {arm.domain}
              </span>
            </div>

            <div style={{ marginTop: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#9ca3af', marginBottom: '6px' }}>
                <span>Surprise ΔS</span>
                <span>{arm.surprise.toFixed(3)} / θ={arm.threshold.toFixed(2)}</span>
              </div>
              <div style={{ height: '6px', backgroundColor: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{
                  width: `${Math.min(100, (arm.surprise / arm.threshold) * 100)}%`,
                  height: '100%',
                  backgroundColor: arm.surprise > arm.threshold ? '#ef4444' : arm.color,
                  transition: 'width 0.3s ease',
                }} />
              </div>
            </div>

            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '11px',
              color: '#6b7280',
              marginTop: '12px',
              paddingTop: '10px',
              borderTop: '1px solid #1e293b',
            }}>
              <span>Silent steps: {arm.silentSteps}</span>
              <span>Escalations: {arm.escalations}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
