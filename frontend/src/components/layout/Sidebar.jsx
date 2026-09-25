import { BarChart3, Database, FileClock, Home, Map, Settings, Upload, Bookmark, Sparkles } from 'lucide-react';

export default function Sidebar({ active, setActive }) {
  const items = [
    { name: 'Dashboard', icon: Home },
    { name: 'Map Analysis', icon: Map, badge: 'Live' },
    { name: 'Upload & Query', icon: Upload },
    { name: 'Query History', icon: FileClock },
    { name: 'Saved Results', icon: Bookmark },
    { name: 'Datasets', icon: Database },
    { name: 'Settings', icon: Settings }
  ];

  return (
    <aside className="sidebar">
      <div className="brand" onClick={() => setActive('Map Analysis')} style={{ cursor: 'pointer' }}>
        <div className="brand-mark">◒</div>
        <div>
          <b>SatQuery <em>AI</em></b>
          <small>Ask. Analyze. Understand Earth.</small>
        </div>
      </div>
      <nav>
        {items.map(({ name, icon: Icon, badge }) => (
          <button
            key={name}
            className={`nav-item ${active === name ? 'active' : ''}`}
            onClick={() => setActive(name)}
          >
            <Icon size={18} />
            <span>{name}</span>
            {badge && <span className="nav-badge">{badge}</span>}
          </button>
        ))}
      </nav>
      <div className="sidebar-footer" onClick={() => setActive('Dashboard')} style={{ cursor: 'pointer' }}>
        <Sparkles size={18} />
        <div>
          <b>EarthDial 4B</b>
          <small>VLM Active</small>
        </div>
      </div>
    </aside>
  );
}
