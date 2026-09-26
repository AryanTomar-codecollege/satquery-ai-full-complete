import { useEffect, useMemo, useRef, useState } from 'react';
import { Image as ImageIcon, Loader2 } from 'lucide-react';
import { postPreview } from '../../api/client';

function featureBoxes(result) {
  return (result?.geojson?.features || [])
    .filter(
      (f) =>
        Array.isArray(f?.properties?.bbox_pixel) &&
        f.properties.bbox_pixel.length === 4
    )
    .map((f, i) => ({
      id: i,
      label: f.properties.label || f.properties.name || 'Detected feature',
      bbox: f.properties.bbox_pixel,
      approximate: f.properties.approximate === true,
    }));
}

function PreviewPane({
  file,
  preview,
  width,
  height,
  boxes,
  showOverlay,
  label,
}) {
  const paneRef = useRef(null);
  const [paneSize, setPaneSize] = useState({ width: 1, height: 1 });

  useEffect(() => {
    if (!paneRef.current) return undefined;

    const update = () => {
      const rect = paneRef.current.getBoundingClientRect();
      setPaneSize({
        width: Math.max(1, rect.width),
        height: Math.max(1, rect.height),
      });
    };

    update();
    const observer = new ResizeObserver(update);
    observer.observe(paneRef.current);
    return () => observer.disconnect();
  }, []);

  if (!file) {
    return (
      <div style={styles.empty}>
        <ImageIcon size={30} />
        <span>Upload a GeoTIFF to inspect</span>
      </div>
    );
  }

  const imageWidth = Math.max(1, Number(width) || 1);
  const imageHeight = Math.max(1, Number(height) || 1);

  // Match the browser's object-fit: contain geometry so overlays land on
  // the actual displayed image rather than on the surrounding letterbox.
  const scale = Math.min(
    paneSize.width / imageWidth,
    paneSize.height / imageHeight
  );
  const displayedWidth = imageWidth * scale;
  const displayedHeight = imageHeight * scale;
  const offsetX = (paneSize.width - displayedWidth) / 2;
  const offsetY = (paneSize.height - displayedHeight) / 2;

  return (
    <div ref={paneRef} style={styles.pane}>
      {preview ? (
        <img
          src={preview}
          alt={file.name}
          style={styles.image}
        />
      ) : (
        <div style={styles.loading}>
          <Loader2 size={24} className="spinner" />
          <span>Creating satellite preview…</span>
        </div>
      )}

      {showOverlay &&
        preview &&
        boxes.map((box) => {
          const [x1, y1, x2, y2] = box.bbox;

          const left = offsetX + x1 * scale;
          const top = offsetY + y1 * scale;
          const boxWidth = Math.max(2, (x2 - x1) * scale);
          const boxHeight = Math.max(2, (y2 - y1) * scale);

          return (
            <div
              key={box.id}
              style={{
                ...styles.box,
                left,
                top,
                width: boxWidth,
                height: boxHeight,
              }}
            >
              <span
                style={{
                  ...styles.label,
                  background: box.approximate ? '#b45309' : '#ef4444',
                }}
              >
                {box.label}
                {box.approximate ? ' · approximate' : ''}
              </span>
            </div>
          );
        })}

      <div style={styles.badge}>{label || file.name}</div>
    </div>
  );
}

export default function ImageAnalysisView({
  files = [],
  resultData,
  viewMode = 'Single View',
  showOverlay = true,
}) {
  const [previews, setPreviews] = useState([]);
  const [active, setActive] = useState(0);
  const [error, setError] = useState('');

  const dims = resultData?.metadata?.image_dimensions || [];

  useEffect(() => {
    let alive = true;
    const urls = [];

    async function load() {
      setError('');
      const next = [];

      for (const file of files.slice(0, 2)) {
        try {
          const url = await postPreview(file);
          urls.push(url);
          next.push(url);
        } catch (e) {
          next.push(null);
          if (alive) setError(e.message);
        }
      }

      if (alive) setPreviews(next);
    }

    setPreviews([]);
    load();

    return () => {
      alive = false;
      urls.forEach(URL.revokeObjectURL);
    };
  }, [files]);

  const boxes = useMemo(() => featureBoxes(resultData), [resultData]);

  const showTwo =
    files.length > 1 &&
    (viewMode === 'Split View' ||
      viewMode === 'Side by Side' ||
      viewMode === 'Swipe');

  return (
    <div style={styles.shell}>
      <div style={styles.toolbar}>
        <div>
          <b>Image Analysis View</b>
          <small>
            Real uploaded GeoTIFF preview · EarthDial evidence overlays
          </small>
        </div>

        <div style={styles.controls}>
          {files.length > 1 &&
            files.map((f, i) => (
              <button
                key={f.name + i}
                onClick={() => setActive(i)}
                style={active === i ? styles.activeBtn : styles.btn}
              >
                Image {i + 1}
              </button>
            ))}

          <span style={styles.evidence}>
            {boxes.length} highlight{boxes.length === 1 ? '' : 's'}
          </span>
        </div>
      </div>

      {error && <div style={styles.notice}>{error}</div>}

      {showTwo ? (
        <div style={styles.grid}>
          {files.slice(0, 2).map((file, i) => {
            const d = dims[i] || { width: 1, height: 1 };

            return (
              <PreviewPane
                key={file.name + i}
                file={file}
                preview={previews[i]}
                width={d.width}
                height={d.height}
                boxes={boxes}
                showOverlay={showOverlay}
                label={`Image ${i + 1} · ${file.name}`}
              />
            );
          })}
        </div>
      ) : (
        <PreviewPane
          file={files[active]}
          preview={previews[active]}
          width={(dims[active] || {}).width || 1}
          height={(dims[active] || {}).height || 1}
          boxes={boxes}
          showOverlay={showOverlay}
          label={files[active]?.name}
        />
      )}

      {files.length > 0 && (
        <div style={styles.footer}>
          {resultData?.geojson?.features?.length
            ? boxes.some((b) => b.approximate)
              ? 'Approximate highlight derived from EarthDial relative-location evidence.'
              : 'AI location evidence is drawn from backend pixel bbox properties.'
            : resultData
              ? 'No location boxes returned.'
              : 'File uploaded — run an analysis to request location evidence.'}
        </div>
      )}
    </div>
  );
}

const styles = {
  shell: {
    flex: 1,
    minHeight: 0,
    height: 'auto',
    background: '#111827',
    borderRadius: 12,
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
    border: '1px solid rgba(255,255,255,.08)',
  },
  toolbar: {
    padding: '10px 12px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
    color: '#fff',
    background: '#0f172a',
    flexShrink: 0,
  },
  controls: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    flexWrap: 'wrap',
  },
  btn: {
    border: '1px solid #334155',
    background: '#1e293b',
    color: '#cbd5e1',
    borderRadius: 6,
    padding: '5px 8px',
    fontSize: 11,
  },
  activeBtn: {
    border: '1px solid #0bb27e',
    background: '#12352e',
    color: '#fff',
    borderRadius: 6,
    padding: '5px 8px',
    fontSize: 11,
  },
  evidence: {
    fontSize: 11,
    color: '#a7f3d0',
    padding: '5px 8px',
    whiteSpace: 'nowrap',
  },
  pane: {
    position: 'relative',
    flex: 1,
    minHeight: 0,
    overflow: 'hidden',
    background: '#020617',
  },
  image: {
    display: 'block',
    width: '100%',
    height: '100%',
    objectFit: 'contain',
    background: '#020617',
  },
  loading: {
    position: 'absolute',
    inset: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    color: '#cbd5e1',
  },
  empty: {
    flex: 1,
    minHeight: 0,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    color: '#94a3b8',
    background: '#020617',
  },
  box: {
    position: 'absolute',
    border: '2px solid #ef4444',
    background: 'rgba(239,68,68,.18)',
    boxSizing: 'border-box',
    pointerEvents: 'none',
    zIndex: 5,
  },
  label: {
    position: 'absolute',
    top: -21,
    left: -2,
    color: '#fff',
    fontSize: 10,
    padding: '2px 4px',
    whiteSpace: 'nowrap',
    borderRadius: 3,
    maxWidth: 220,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  notice: {
    padding: '7px 12px',
    background: '#3f2a10',
    color: '#fed7aa',
    fontSize: 11,
    flexShrink: 0,
  },
  badge: {
    position: 'absolute',
    top: 10,
    left: 10,
    padding: '5px 8px',
    borderRadius: 6,
    background: 'rgba(15,23,42,.8)',
    color: '#fff',
    fontSize: 11,
    maxWidth: '70%',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    zIndex: 10,
  },
  footer: {
    padding: '8px 12px',
    fontSize: 11,
    color: '#cbd5e1',
    background: '#0f172a',
    flexShrink: 0,
    minHeight: 32,
    display: 'flex',
    alignItems: 'center',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 2,
    flex: 1,
    minHeight: 0,
  },
};
