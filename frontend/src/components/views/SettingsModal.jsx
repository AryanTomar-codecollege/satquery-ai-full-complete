import { X, Server, Sliders, Check } from 'lucide-react';
import { useState } from 'react';
import { getApiBaseUrl } from '../../api/client';

export default function SettingsModal({ isOpen, onClose, onToast }) {
  const [backendUrl, setBackendUrl] = useState(() => getApiBaseUrl());
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [mapStyle, setMapStyle] = useState(() => localStorage.getItem('satquery.mapStyle') || 'satellite');

  if (!isOpen) return null;

  const handleSave = () => {
    localStorage.setItem('satquery.mapStyle', mapStyle);
    onToast?.('Local settings saved. Restart with VITE_API_BASE_URL to change the API endpoint.');
    onClose?.();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <Sliders size={20} color="#0bb27e" />
            <h2>SatQuery AI Settings</h2>
          </div>
          <button className="close-btn" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label>Backend API Base URL</label>
            <div className="input-with-icon">
              <Server size={16} />
              <input value={backendUrl} onChange={(e) => setBackendUrl(e.target.value)} />
            </div>
            <small className="settings-help">The current value comes from VITE_API_BASE_URL.</small>
          </div>

          <div className="form-group">
            <label>Map Style</label>
            <div className="input-with-icon">
              <select value={mapStyle} onChange={(e) => setMapStyle(e.target.value)}>
                <option value="satellite">Satellite</option>
                <option value="osm">Street Map</option>
                <option value="topo">Topographic</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Voice Input</label>
            <button
              type="button"
              className={`toggle-switch-btn ${voiceEnabled ? 'active' : ''}`}
              onClick={() => setVoiceEnabled((v) => !v)}
            >
              {voiceEnabled ? 'ENABLED' : 'DISABLED'}
            </button>
          </div>

          <div className="settings-note">
            EarthDial, Ngrok, OmniRoute, and model credentials remain backend/Kaggle configuration. They are not exposed to the browser.
          </div>
        </div>

        <div className="modal-footer">
          <button className="secondary-btn" onClick={onClose}>Cancel</button>
          <button className="primary-action-btn" onClick={handleSave}>
            <Check size={16} /> Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}
