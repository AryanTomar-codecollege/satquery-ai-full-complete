import { Database, Eye, Search } from 'lucide-react';
import { useMemo, useState } from 'react';

const datasets = [
  { name: 'ONERA Satellite Change Detection', type: 'Bi-temporal optical', bands: 'Multispectral', resolution: 'Dataset dependent', source: 'OSCD / Kaggle', size: 'External' },
  { name: 'Sentinel-1 SAR', type: 'Synthetic Aperture Radar', bands: 'VV / VH', resolution: '10m class', source: 'ESA Copernicus', size: 'External' },
  { name: 'Sentinel-2', type: 'Optical multispectral', bands: 'Multispectral', resolution: '10m class', source: 'ESA Copernicus', size: 'External' }
];

export default function DatasetsView({ onToast, onGoToMap }) {
  const [search, setSearch] = useState('');
  const filtered = useMemo(
    () => datasets.filter((d) => `${d.name} ${d.type}`.toLowerCase().includes(search.toLowerCase())),
    [search]
  );

  return (
    <div className="view-container">
      <div className="view-header">
        <div>
          <h1>Dataset Guidance</h1>
          <p>Reference datasets useful for preparing GeoTIFF inputs. Files are uploaded through Map Analysis.</p>
        </div>
        <div className="search-filter-box">
          <Search size={16} />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search datasets..." />
        </div>
      </div>

      <div className="datasets-grid">
        {filtered.map((ds) => (
          <div key={ds.name} className="dataset-card">
            <div className="dataset-head">
              <div className="ds-icon"><Database size={20} /></div>
              <div>
                <h3>{ds.name}</h3>
                <span className="ds-type">{ds.type}</span>
              </div>
            </div>
            <div className="dataset-details">
              <div><span>Spectral Bands</span><b>{ds.bands}</b></div>
              <div><span>Spatial Resolution</span><b>{ds.resolution}</b></div>
              <div><span>Provider / Source</span><b>{ds.source}</b></div>
              <div><span>Availability</span><b>{ds.size}</b></div>
            </div>
            <div className="dataset-footer">
              <button className="secondary-btn" onClick={() => onToast?.(`Reference: ${ds.source}`)}>
                <Eye size={15} /> Inspect
              </button>
              <button className="primary-action-btn" onClick={() => { onToast?.('Go to Map Analysis to upload a GeoTIFF from this dataset.'); onGoToMap?.(); }}>
                Use in Analysis ↗
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
