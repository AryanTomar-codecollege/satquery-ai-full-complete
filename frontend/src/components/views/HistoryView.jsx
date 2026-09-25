import { Bookmark, CheckCircle2, FileClock, Search, Trash2, ArrowUpRight } from 'lucide-react';
import { useMemo, useState } from 'react';

export default function HistoryView({
  isSaved = false,
  records = [],
  onLoad,
  onDelete,
  onSave,
  onGoToMap,
  onToast
}) {
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = useMemo(() => {
    const needle = searchTerm.toLowerCase();
    return records.filter((item) =>
      `${item.query || ''} ${item.task || ''} ${item.answer || ''}`.toLowerCase().includes(needle)
    );
  }, [records, searchTerm]);

  return (
    <div className="view-container">
      <div className="view-header">
        <div>
          <h1>{isSaved ? 'Saved Results & Bookmarks' : 'Query Execution History'}</h1>
          <p>
            {isSaved
              ? 'Local saved responses from real backend analyses'
              : 'Recent queries, answers, confidence, and routing information'}
          </p>
        </div>
        <div className="search-filter-box">
          <Search size={16} />
          <input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search queries..."
          />
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state">
          <FileClock size={24} />
          <p>{isSaved ? 'No saved results yet.' : 'No real analyses have been run yet.'}</p>
          <button className="secondary-btn" onClick={onGoToMap}>Go to Map Analysis</button>
        </div>
      ) : (
        <div className="history-list">
          {filtered.map((item) => (
            <div key={item.id} className="history-card">
              <div className="history-card-main">
                <div className="history-head">
                  <span className="task-pill">{item.task || 'analysis'}</span>
                  <span className="history-date">
                    {item.timestamp ? new Date(item.timestamp).toLocaleString() : '—'}
                  </span>
                  <span className="status-badge">
                    <CheckCircle2 size={13} /> Completed
                  </span>
                </div>
                <h3 className="history-query-text">{item.query}</h3>
                <div className="history-meta">
                  <span>Confidence: <strong>{Math.round((item.confidence || 0) * 100)}%</strong></span>
                  <span>Router: <strong>{item.router || 'deterministic'}</strong></span>
                </div>
              </div>

              <div className="history-actions">
                {!isSaved && (
                  <button
                    className="action-icon-btn"
                    title="Save result"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSave?.(item);
                      onToast?.('Result saved locally.');
                    }}
                  >
                    <Bookmark size={17} />
                  </button>
                )}
                <button
                  className="action-icon-btn delete-btn"
                  title="Delete record"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete?.(item.id);
                  }}
                >
                  <Trash2 size={17} />
                </button>
                <button
                  className="load-btn"
                  onClick={() => {
                    onLoad?.(item);
                    onGoToMap?.();
                  }}
                >
                  Load Result <ArrowUpRight size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
