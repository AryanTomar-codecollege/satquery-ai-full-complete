import { useState } from 'react';
import {
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  FileJson,
  FileText,
  MapPin,
  Bookmark
} from 'lucide-react';

function downloadJson(filename, value) {
  const blob = new Blob([JSON.stringify(value ?? {}, null, 2)], {
    type: 'application/json'
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function firstCoordinate(value) {
  if (!value) return null;
  if (typeof value === 'object' && Number.isFinite(value.lat) && Number.isFinite(value.lng)) {
    return value;
  }
  if (Array.isArray(value) && value.length >= 2 && Number.isFinite(Number(value[0])) && Number.isFinite(Number(value[1]))) {
    return { lng: Number(value[0]), lat: Number(value[1]) };
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      const found = firstCoordinate(item);
      if (found) return found;
    }
  }
  return null;
}

function coordinateFromGeoJSON(geojson) {
  const features = geojson?.features || [];
  for (const feature of features) {
    const found = firstCoordinate(feature?.geometry?.coordinates);
    if (found) return found;
  }
  return null;
}

export default function ResultsPanel({
  result,
  onFocusArea,
  onToast,
  onSave
}) {
  const [activeTab, setActiveTab] = useState('Answer');
  const [traceOpen, setTraceOpen] = useState(true);

  if (!result) {
    return (
      <aside className="results-panel">
        <div className="result-head">
          <div>
            <h2>AI Analysis Result</h2>
            <span>Waiting for an analysis</span>
          </div>
        </div>
        <section className="result-card">
          <p>Upload a GeoTIFF, enter a question, and run an analysis. Results from the real backend will appear here.</p>
        </section>
      </aside>
    );
  }

  const trace = result.execution_trace || {};
  const metadata = result.metadata || {};
  const geojson = result.geojson || { type: 'FeatureCollection', features: [] };
  const coordinate = coordinateFromGeoJSON(geojson);
  const featureCount = Array.isArray(geojson.features) ? geojson.features.length : 0;

  const openMap = () => {
    if (!coordinate) {
      onToast?.('No coordinates are available in the backend GeoJSON result.');
      return;
    }
    const url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${coordinate.lat},${coordinate.lng}`)}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const report = result.report || {
    title: 'SatQuery AI Analysis Report',
    query: '',
    answer: result.answer,
    confidence: result.confidence,
    execution_trace: trace,
    metadata
  };

  return (
    <aside className="results-panel">
      <div className="result-head">
        <div>
          <h2>AI Analysis Result</h2>
          <span>
            {report.timestamp
              ? new Date(report.timestamp).toLocaleString()
              : 'Backend response'}
          </span>
        </div>
        <span className="status-pill">
          <CheckCircle2 size={15} /> Completed
        </span>
      </div>

      <div className="tabs">
        {['Answer', 'Execution Trace', 'Metadata'].map((tab) => (
          <button
            key={tab}
            className={`tab ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'Answer' && (
        <>
          <section className="result-card">
            <p>{result.answer}</p>
            <div className="confidence-head">
              <b>Confidence</b>
              <strong>{Math.round((result.confidence || 0) * 100)}%</strong>
            </div>
            <div className="progress">
              <span style={{ width: `${Math.max(0, Math.min(100, (result.confidence || 0) * 100))}%` }} />
            </div>
          </section>

          <section className="result-card">
            <h3>
              <span>Spatial Evidence</span>
              <strong>{featureCount} feature{featureCount === 1 ? '' : 's'}</strong>
            </h3>
            <div className="trace">
              {featureCount > 0 ? (
                <div>
                  <span>GeoJSON overlay</span>
                  <b>Available on map</b>
                </div>
              ) : (
                <div>
                  <span>GeoJSON overlay</span>
                  <b>No spatial features returned</b>
                </div>
              )}
            </div>
          </section>
        </>
      )}

      {activeTab === 'Execution Trace' && (
        <section className="result-card">
          <h3
            onClick={() => setTraceOpen((open) => !open)}
            style={{ cursor: 'pointer', userSelect: 'none' }}
          >
            <span>Execution Trace</span>
            {traceOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </h3>
          {traceOpen && (
            <div className="trace">
              <div><span>Selected Task</span><b>{trace.selected_task || '—'}</b></div>
              <div><span>Tools Used</span><b>{trace.tools_used?.join(', ') || '—'}</b></div>
              <div><span>Model Used</span><b>{trace.model_used || '—'}</b></div>
              <div><span>Router</span><b>{trace.router || '—'}</b></div>
              <div><span>Router Reason</span><b>{trace.router_reason || '—'}</b></div>
              <div><span>Parameters</span><b>{JSON.stringify(trace.parameters || {})}</b></div>
            </div>
          )}
        </section>
      )}

      {activeTab === 'Metadata' && (
        <section className="result-card">
          <div className="trace" style={{ marginTop: 0 }}>
            <div><span>Images</span><b>{metadata.num_images ?? '—'}</b></div>
            <div><span>Modalities</span><b>{metadata.modalities?.join(' + ') || '—'}</b></div>
            <div><span>CRS</span><b>{metadata.crs || '—'}</b></div>
          </div>
        </section>
      )}

      <h3 className="download-title">Results</h3>
      <div className="download-grid">
        <button
          onClick={() => {
            downloadJson(`satquery_geojson_${Date.now()}.json`, geojson);
            onToast?.('GeoJSON downloaded.');
          }}
        >
          <FileJson size={16} /> GeoJSON
        </button>
        <button
          onClick={openMap}
          disabled={!coordinate}
          title={coordinate ? 'Open the first returned coordinate in Google Maps' : 'No coordinates in GeoJSON'}
        >
          <MapPin size={16} /> Open Map
        </button>
        <button
          className="wide"
          onClick={() => {
            downloadJson(`satquery_report_${Date.now()}.json`, report);
            onToast?.('Analysis report downloaded.');
          }}
        >
          <FileText size={16} /> Report (JSON)
        </button>
        <button
          className="wide"
          onClick={() => onSave?.()}
        >
          <Bookmark size={16} /> Save Result
        </button>
      </div>
    </aside>
  );
}
