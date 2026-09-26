import { useEffect, useMemo, useState } from 'react';

const previewCache = new Map();
const previewPending = new Map();

function previewKey(file) {
  return `${file?.name || ''}:${file?.size || 0}:${file?.lastModified || 0}`;
}
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
      bbox: f.properties.bbox_pixel.map(Number),
      approximate: f.properties.approximate === true,
    }))
    .filter((f) => f.bbox.every(Number.isFinite));
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
  const [naturalSize, setNaturalSize] = useState({
    width: Number(width) || 0,
    height: Number(height) || 0,
  });

  useEffect(() => {
    setNaturalSize({
      width: Number(width) || 0,
      height: Number(height) || 0,
    });
  }, [width, height]);

  if (!file) {
    return (
      <div style={styles.empty}>
        <ImageIcon size={30} />
        <span>Upload a GeoTIFF to inspect</span>
      </div>
    );
  }

  const imageWidth = naturalSize.width;
  const imageHeight = naturalSize.height;

  return (
    <div style={styles.pane}>
      {preview ? (
        <>
          <img
            src={preview}
            alt={file.name}
            style={styles.image}
            onLoad={(event) => {
              const image = event.currentTarget;

              if (!imageWidth || !imageHeight) {
                setNaturalSize({
                  width: image.naturalWidth,
                  height: image.naturalHeight,
                });
              }
            }}
          />

          {showOverlay && imageWidth > 0 && imageHeight > 0 && (
            <svg
              aria-label="AI spatial evidence overlay"
              viewBox={`0 0 ${imageWidth} ${imageHeight}`}
              preserveAspectRatio="xMidYMid meet"
              style={styles.overlay}
            >
              {boxes.map((box) => {
                const [rawX1, rawY1, rawX2, rawY2] = box.bbox;

                const x1 = Math.max(0, Math.min(imageWidth, rawX1));
                const y1 = Math.max(0, Math.min(imageHeight, rawY1));
                const x2 = Math.max(0, Math.min(imageWidth, rawX2));
                const y2 = Math.max(0, Math.min(imageHeight, rawY2));

                const x = Math.min(x1, x2);
                const y = Math.min(y1, y2);
                const w = Math.abs(x2 - x1);
                const h = Math.abs(y2 - y1);

                if (w <= 0 || h <= 0) return null;

                return (
                  <g key={box.id}>
                    <rect
                      x={x}
                      y={y}
                      width={w}
                      height={h}
                      fill="#ef4444"
                      fillOpacity="0.10"
                      stroke="#ef4444"
                      strokeWidth="2.5"
                      vectorEffect="non-scaling-stroke"
                    />

                    <text
                      x={x + 8}
                      y={Math.max(20, y + 18)}
                      fill="#ffffff"
                      fontSize={Math.max(
                        16,
                        Math.min(imageWidth, imageHeight) / 35
                      )}
                      fontWeight="700"
                      paintOrder="stroke"
                      stroke="#111827"
                      strokeWidth="4"
                    >
                      {box.label}
                    </text>
                  </g>
                );
              })}
            </svg>
          )}
        </>
      ) : (
        <div style={styles.loading}>
          <Loader2 size={24} className="spinner" />
          <span>Creating satellite preview…</span>
        </div>
      )}

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

    async function getPreview(file) {
      const key = previewKey(file);

      // Keep the object URL alive across React view changes. Navigation in this
      // SPA unmounts/remounts ImageAnalysisView, but the uploaded file has not
      // changed, so the preview should not be regenerated.
      if (previewCache.has(key)) {
        return previewCache.get(key);
      }

      if (!previewPending.has(key)) {
        previewPending.set(
          key,
          postPreview(file).then((url) => {
            previewCache.set(key, url);
            previewPending.delete(key);
            return url;
          }).catch((error) => {
            previewPending.delete(key);
            throw error;
          })
        );
      }

      return previewPending.get(key);
    }

    async function load() {
      setError('');

      const currentFiles = files.slice(0, 2);
      const initial = currentFiles.map((file) => previewCache.get(previewKey(file)) || null);

      // Immediately show any cached previews instead of flashing the loading
      // state when returning from History/Saved Results/etc.
      if (alive) {
        setPreviews(initial);
      }

      const next = [...initial];

      for (let i = 0; i < currentFiles.length; i += 1) {
        if (next[i]) continue;

        try {
          next[i] = await getPreview(currentFiles[i]);
          if (alive) {
            setPreviews([...next]);
          }
        } catch (e) {
          next[i] = null;
          if (alive) {
            setError(e.message);
            setPreviews([...next]);
          }
        }
      }
    }

    load();

    // Do not revoke cached object URLs here. They intentionally survive
    // navigation/remounts and are replaced only when the uploaded file
    // identity changes.
    return () => {
      alive = false;
    };
  }, [files]);

  const boxes = useMemo(
    () => featureBoxes(resultData),
    [resultData]
  );

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
            const d = dims[i] || {};

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
          width={(dims[active] || {}).width}
          height={(dims[active] || {}).height}
          boxes={boxes}
          showOverlay={showOverlay}
          label={files[active]?.name}
        />
      )}

      {files.length > 0 && (
        <div style={styles.footer}>
          {resultData?.geojson?.features?.length
            ? boxes.some((b) => b.approximate)
              ? boxes.some((b) => b.label && b.label.toLowerCase().includes('water'))
                ? 'Approximate red highlight derived from image-grounded water evidence.'
                : 'Approximate red highlight derived from model relative-location evidence.'
              : 'Red highlights use backend spatial evidence; overlapping and nearby regions are merged when appropriate.'
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
    objectPosition: 'center',
    background: '#020617',
  },
  overlay: {
    position: 'absolute',
    inset: 0,
    width: '100%',
    height: '100%',
    pointerEvents: 'none',
    zIndex: 5,
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
