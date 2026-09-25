import { Activity, Cpu, Database, ArrowRight } from 'lucide-react';

export default function DashboardView({
  latestResult,
  backendOnline,
  earthDialOnline,
  omniRouteActive,
  onGoToMap
}) {
  const stats = [
    {
      title: 'Backend',
      value: backendOnline ? 'Connected' : 'Offline',
      change: 'FastAPI',
      icon: Activity
    },
    {
      title: 'EarthDial',
      value: earthDialOnline ? 'Available' : 'Unavailable',
      change: 'Kaggle / Ngrok',
      icon: Cpu
    },
    {
      title: 'Last Images',
      value: latestResult?.metadata?.num_images ?? '—',
      change: 'Latest real response',
      icon: Database
    }
  ];

  return (
    <div className="view-container">
      <div className="view-header">
        <div>
          <h1>SatQuery AI Dashboard</h1>
          <p>Live status and the latest response from the real analysis pipeline.</p>
        </div>
        <button className="primary-action-btn" onClick={onGoToMap}>
          Launch Map Analysis <ArrowRight size={16} />
        </button>
      </div>

      <div className="stats-grid">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.title} className="stat-card">
              <div className="stat-icon">
                <Icon size={22} />
              </div>
              <div className="stat-info">
                <span className="stat-title">{stat.title}</span>
                <b className="stat-value">{stat.value}</b>
                <small className="stat-change">{stat.change}</small>
              </div>
            </div>
          );
        })}
      </div>

      <div className="dashboard-sections">
        <div className="dash-card">
          <div className="dash-card-head">
            <h3>Latest Analysis</h3>
          </div>
          {latestResult ? (
            <>
              <p className="dashboard-answer">{latestResult.answer}</p>
              <div className="specs-list">
                <div className="spec-item"><span>Task</span><b>{latestResult.execution_trace?.selected_task || '—'}</b></div>
                <div className="spec-item"><span>Router</span><b>{latestResult.execution_trace?.router || '—'}</b></div>
                <div className="spec-item"><span>Confidence</span><b>{Math.round((latestResult.confidence || 0) * 100)}%</b></div>
              </div>
            </>
          ) : (
            <p className="dashboard-empty">No live analysis has been run in this session yet.</p>
          )}
        </div>

        <div className="dash-card">
          <div className="dash-card-head">
            <h3>Pipeline Status</h3>
          </div>
          <div className="specs-list">
            <div className="spec-item"><span>FastAPI</span><b>{backendOnline ? 'Connected' : 'Offline'}</b></div>
            <div className="spec-item"><span>EarthDial</span><b>{earthDialOnline ? 'Connected' : 'Not confirmed'}</b></div>
            <div className="spec-item"><span>OmniRoute</span><b>{omniRouteActive ? 'Used on last run' : 'Not used on last run'}</b></div>
            <div className="spec-item"><span>Frontend → Kaggle direct</span><b>Never</b></div>
          </div>
        </div>
      </div>
    </div>
  );
}
