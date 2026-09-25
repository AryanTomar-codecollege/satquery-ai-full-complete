import { useState, useRef, useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMap, useMapEvents, Pane, Polygon, Polyline, CircleMarker } from 'react-leaflet';
import { Layers, Pencil, Maximize2, Minimize2, MapPin, ArrowLeftRight, Trash2, CheckCircle2 } from 'lucide-react';

const DEFAULT_CENTER = [30.9012, 75.6576];
const DEFAULT_ZOOM = 14;

// Drawing mode click handler component
function DrawingController({ isDrawing, onAddPoint }) {
  const map = useMap();

  useEffect(() => {
    if (isDrawing) {
      map.getContainer().style.cursor = 'crosshair';
    } else {
      map.getContainer().style.cursor = '';
    }
  }, [isDrawing, map]);

  useMapEvents({
    click(e) {
      if (!isDrawing) return;
      const { lat, lng } = e.latlng;
      onAddPoint([parseFloat(lat.toFixed(5)), parseFloat(lng.toFixed(5))]);
    }
  });

  return null;
}

// Resize controller to automatically invalidate map size on container dimensions change
function ResizeController() {
  const map = useMap();

  useEffect(() => {
    const handleResize = () => {
      map.invalidateSize();
    };

    const container = map.getContainer();
    let observer;
    if (window.ResizeObserver && container) {
      observer = new ResizeObserver(() => {
        map.invalidateSize();
      });
      observer.observe(container);
    }

    window.addEventListener('resize', handleResize);
    return () => {
      if (observer) observer.disconnect();
      window.removeEventListener('resize', handleResize);
    };
  }, [map]);

  return null;
}

// Map controller helper to support reset view and flyTo
function MapController({ resetTrigger, focusedCoord }) {
  const map = useMap();

  useEffect(() => {
    if (resetTrigger) {
      map.flyTo(DEFAULT_CENTER, DEFAULT_ZOOM, { duration: 1.2 });
    }
  }, [resetTrigger, map]);

  useEffect(() => {
    if (focusedCoord) {
      map.flyTo([focusedCoord.lat, focusedCoord.lng], 15, { duration: 1.0 });
    }
  }, [focusedCoord, map]);

  return null;
}

// Controller to dynamically clip Leaflet layers using layer-space coordinates
function CurtainClipController({ splitPos, isSplitMode, activeLayers, layer1Ref, layer2Ref, isSwapped }) {
  const map = useMap();

  useEffect(() => {
    const updateClip = () => {
      if (!map) return;
      let size;
      try {
        size = map.getSize();
      } catch (e) {
        return;
      }
      if (!size || !size.x || !size.y) return;

      const nw = map.containerPointToLayerPoint([0, 0]);
      const se = map.containerPointToLayerPoint(size);
      const clipX = nw.x + (size.x * splitPos) / 100;

      const leftPane = map.getPane('left-pane');
      const rightPane = map.getPane('right-pane');
      const layer1El = layer1Ref?.current?.getContainer?.() || leftPane;
      const layer2El = layer2Ref?.current?.getContainer?.() || rightPane;

      if (leftPane) {
        if (isSplitMode && activeLayers.image2022 && activeLayers.image2024) {
          const rect = `rect(${nw.y}px, ${clipX}px, ${se.y}px, ${nw.x}px)`;
          leftPane.style.clip = rect;
          if (layer1El && layer1El !== leftPane) layer1El.style.clip = rect;
        } else {
          leftPane.style.clip = 'auto';
          if (layer1El && layer1El !== leftPane) layer1El.style.clip = 'auto';
        }
        leftPane.style.filter = isSwapped
          ? 'contrast(1.18) saturate(1.3) hue-rotate(18deg) brightness(1.04)'
          : 'none';
      }

      if (rightPane) {
        if (isSplitMode && activeLayers.image2022 && activeLayers.image2024) {
          const rect = `rect(${nw.y}px, ${se.x}px, ${se.y}px, ${clipX}px)`;
          rightPane.style.clip = rect;
          if (layer2El && layer2El !== rightPane) layer2El.style.clip = rect;
        } else {
          rightPane.style.clip = 'auto';
          if (layer2El && layer2El !== rightPane) layer2El.style.clip = 'auto';
        }
        rightPane.style.filter = isSwapped
          ? 'none'
          : 'contrast(1.18) saturate(1.3) hue-rotate(18deg) brightness(1.04)';
      }
    };

    updateClip();

    map.on('move', updateClip);
    map.on('zoom', updateClip);
    map.on('resize', updateClip);

    return () => {
      map.off('move', updateClip);
      map.off('zoom', updateClip);
      map.off('resize', updateClip);
    };
  }, [map, splitPos, isSplitMode, activeLayers, layer1Ref, layer2Ref, isSwapped]);

  return null;
}

export default function MapView({
  viewMode = 'Split View',
  mapStyle = 'satellite',
  onMapStyleChange,
  resultData,
  resetTrigger,
  focusedCoord,
  showOverlay = true,
  onToggleOverlay,
  isDrawing = false,
  onToggleDrawing,
  onAOIComplete,
  onAOIClear
}) {
  const [splitPos, setSplitPos] = useState(50); // percentage 0-100
  const [isDragging, setIsDragging] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isSwapped, setIsSwapped] = useState(false);
  const [showLayerMenu, setShowLayerMenu] = useState(false);
  const [drawnPoints, setDrawnPoints] = useState([]);
  const [savedAOI, setSavedAOI] = useState(null);
  const [activeLayers, setActiveLayers] = useState({
    image2022: true,
    image2024: true,
    aiPolygons: true,
    cloudMask: false
  });
  const [coords, setCoords] = useState({ lat: '30.9012', lng: '75.6576' });
  
  const containerRef = useRef(null);

  // Handle curtain drag across mouse / touch / pointer
  const handlePointerDown = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  useEffect(() => {
    if (!isDragging) return;

    const handlePointerMove = (e) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const clientX = e.clientX ?? (e.touches && e.touches[0]?.clientX);
      if (clientX === undefined) return;
      const x = clientX - rect.left;
      const percentage = Math.max(1, Math.min(99, (x / rect.width) * 100));
      setSplitPos(percentage);
    };

    const handlePointerUp = () => {
      setIsDragging(false);
    };

    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerUp);
    window.addEventListener('pointercancel', handlePointerUp);
    window.addEventListener('mousemove', handlePointerMove);
    window.addEventListener('mouseup', handlePointerUp);
    window.addEventListener('touchmove', handlePointerMove);
    window.addEventListener('touchend', handlePointerUp);

    return () => {
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
      window.removeEventListener('pointercancel', handlePointerUp);
      window.removeEventListener('mousemove', handlePointerMove);
      window.removeEventListener('mouseup', handlePointerUp);
      window.removeEventListener('touchmove', handlePointerMove);
      window.removeEventListener('touchend', handlePointerUp);
    };
  }, [isDragging]);

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen?.().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen?.().catch(() => {});
      setIsFullscreen(false);
    }
  };

  useEffect(() => {
    const onFsChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', onFsChange);
    return () => document.removeEventListener('fullscreenchange', onFsChange);
  }, []);

  const geoStyle = useMemo(() => ({
    color: '#ef4444',
    weight: 2.5,
    fillColor: '#ef4444',
    fillOpacity: 0.38,
    dashArray: '3'
  }), []);

  const satelliteTileUrl = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";
  const osmTileUrl = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
  const topoTileUrl = "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png";

  const getTileUrl = () => {
    if (mapStyle === 'topo') return topoTileUrl;
    if (mapStyle === 'osm') return osmTileUrl;
    return satelliteTileUrl;
  };

  const isSplitMode = viewMode === 'Split View' || viewMode === 'Swipe';

  const layer1Ref = useRef(null);
  const layer2Ref = useRef(null);

  const handleAddDrawnPoint = (point) => {
    setDrawnPoints((prev) => [...prev, point]);
  };

  const handleFinishDrawing = () => {
    if (drawnPoints.length >= 3) {
      setSavedAOI(drawnPoints);
      onAOIComplete?.(drawnPoints);
    }
    onToggleDrawing?.(false);
  };

  const handleClearDrawing = () => {
    setDrawnPoints([]);
    setSavedAOI(null);
    onAOIClear?.();
  };

  return (
    <div
      ref={containerRef}
      className={`map-shell ${isFullscreen ? 'fullscreen' : ''} ${isDragging ? 'is-dragging' : ''}`}
      onMouseMove={(e) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        const relY = (e.clientY - rect.top) / rect.height;
        const relX = (e.clientX - rect.left) / rect.width;
        const lat = (30.915 - relY * 0.03).toFixed(4);
        const lng = (75.64 + relX * 0.035).toFixed(4);
        setCoords({ lat, lng });
      }}
    >
      {/* Top Left: Image 1 Badge */}
      <div className="map-label top-left" style={{ opacity: splitPos > 10 ? 1 : 0 }}>
        <div className="label-title">{isSwapped ? 'Image 2 · 2024' : 'Image 1 · 2022'}</div>
        <div className="label-sub">{isSwapped ? 'Sentinel-2 (Optical)' : 'Sentinel-2 (Optical)'}</div>
        <div className="label-date">{isSwapped ? '10 Mar 2024' : '15 Mar 2022'}</div>
      </div>

      {/* Top Right: Image 2 Badge & Fullscreen Button */}
      <div className="map-top-right-bar">
        {isSplitMode && (
          <div className="map-label top-right" style={{ opacity: splitPos < 90 ? 1 : 0 }}>
            <div className="label-title">{isSwapped ? 'Image 1 · 2022' : 'Image 2 · 2024'}</div>
            <div className="label-sub">{isSwapped ? 'Sentinel-2 (Optical)' : 'Sentinel-2 (Optical)'}</div>
            <div className="label-date">{isSwapped ? '15 Mar 2022' : '10 Mar 2024'}</div>
          </div>
        )}
        <button
          className="map-corner-btn"
          onClick={toggleFullscreen}
          title={isFullscreen ? "Exit Fullscreen" : "Expand Fullscreen"}
        >
          {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
        </button>
      </div>

      {/* Main Leaflet Map with two layers and dynamic clipping */}
      <MapContainer
        center={DEFAULT_CENTER}
        zoom={DEFAULT_ZOOM}
        zoomControl={false}
        className="leaflet-map"
      >
        <MapController
          resetTrigger={resetTrigger}
          focusedCoord={focusedCoord}
        />

        <ResizeController />

        {/* Interactive Drawing Handler */}
        <DrawingController
          isDrawing={isDrawing}
          onAddPoint={handleAddDrawnPoint}
        />
        
        {/* Clip controller dynamically clipping left and right panes */}
        <CurtainClipController
          splitPos={splitPos}
          isSplitMode={isSplitMode}
          activeLayers={activeLayers}
          layer1Ref={layer1Ref}
          layer2Ref={layer2Ref}
          isSwapped={isSwapped}
        />

        {/* Layer 1: Left / Baseline (2022 Base) */}
        {activeLayers.image2022 && (
          <Pane name="left-pane" style={{ zIndex: 200 }}>
            <TileLayer
              ref={layer1Ref}
              attribution="Tiles &copy; Esri, Maxar, EarthDial (2022 Base)"
              url={getTileUrl()}
              pane="left-pane"
            />
          </Pane>
        )}

        {/* Layer 2: Right / Comparison (2024 Target with visual adjustment) */}
        {activeLayers.image2024 && (
          <Pane name="right-pane" style={{ zIndex: 201 }}>
            <TileLayer
              ref={layer2Ref}
              attribution="Tiles &copy; Esri, Maxar, EarthDial (2024 Target)"
              url={getTileUrl()}
              pane="right-pane"
            />
          </Pane>
        )}

        {/* Render AI Result GeoJSON features (above imagery in overlayPane) */}
        {showOverlay && activeLayers.aiPolygons && resultData?.geojson && (
          <GeoJSON
            key={JSON.stringify(resultData.geojson)}
            data={resultData.geojson}
            style={geoStyle}
            onEachFeature={(feature, layer) => {
              if (feature.properties?.name) {
                layer.bindPopup(
                  `<div style="font-family:inherit;font-size:12px;padding:4px">
                    <strong style="color:#ef4444">${feature.properties.name}</strong>
                    <div style="font-size:10px;color:#555;margin-top:4px">${feature.properties.change_type || 'Detected Anomaly'}</div>
                  </div>`
                );
              }
            }}
          />
        )}

        {/* Live Drawing Points & Polygons */}
        {isDrawing && drawnPoints.length > 0 && (
          <>
            {drawnPoints.map((pt, idx) => (
              <CircleMarker
                key={idx}
                center={pt}
                radius={6}
                pathOptions={{ color: '#0bb27e', fillColor: '#ffffff', fillOpacity: 1, weight: 2.5 }}
              />
            ))}
            {drawnPoints.length >= 2 && drawnPoints.length < 3 && (
              <Polyline
                positions={drawnPoints}
                pathOptions={{ color: '#0bb27e', weight: 2.5, dashArray: '5, 5' }}
              />
            )}
            {drawnPoints.length >= 3 && (
              <Polygon
                positions={drawnPoints}
                pathOptions={{ color: '#0bb27e', fillColor: '#0bb27e', fillOpacity: 0.28, weight: 2.5, dashArray: '4, 4' }}
              />
            )}
          </>
        )}

        {/* Saved User AOI Polygon */}
        {!isDrawing && savedAOI && (
          <Polygon
            positions={savedAOI}
            pathOptions={{ color: '#0bb27e', fillColor: '#0bb27e', fillOpacity: 0.2, weight: 2.5 }}
          />
        )}
      </MapContainer>

      {/* Interactive Draggable Curtain Divider */}
      {isSplitMode && (
        <div
          className={`curtain ${isDragging ? 'dragging' : ''}`}
          style={{ left: `${splitPos}%` }}
          onPointerDown={handlePointerDown}
          onMouseDown={handlePointerDown}
          title="Drag slider left/right to compare temporal imagery"
        >
          <div className="curtain-handle">
            <span>&lt;</span>
            <span>&gt;</span>
          </div>
        </div>
      )}

      {/* Bottom Left: Vertical Action Stack */}
      <div className="map-bottom-left-stack">
        <button
          className="map-stack-btn"
          onClick={() => {
            const mapContainer = containerRef.current?.querySelector('.leaflet-container');
            if (mapContainer && mapContainer._leaflet_map) {
              mapContainer._leaflet_map.zoomIn();
            }
          }}
          title="Zoom In"
        >
          +
        </button>
        <button
          className="map-stack-btn"
          onClick={() => {
            const mapContainer = containerRef.current?.querySelector('.leaflet-container');
            if (mapContainer && mapContainer._leaflet_map) {
              mapContainer._leaflet_map.zoomOut();
            }
          }}
          title="Zoom Out"
        >
          −
        </button>

        {/* Layer toggle button & menu */}
        <div style={{ position: 'relative' }}>
          <button
            className={`map-stack-btn ${showLayerMenu ? 'btn-active' : ''}`}
            onClick={() => setShowLayerMenu(!showLayerMenu)}
            title="Layer Settings & Overlays"
          >
            <Layers size={16} />
          </button>
          {showLayerMenu && (
            <div className="layer-menu-popover upward">
              <div className="popover-title">Map Layers</div>
              <label className="layer-option">
                <input
                  type="checkbox"
                  checked={activeLayers.image2022}
                  onChange={(e) => setActiveLayers({ ...activeLayers, image2022: e.target.checked })}
                />
                <span>Sentinel-2 (2022 Base)</span>
              </label>
              <label className="layer-option">
                <input
                  type="checkbox"
                  checked={activeLayers.image2024}
                  onChange={(e) => setActiveLayers({ ...activeLayers, image2024: e.target.checked })}
                />
                <span>Sentinel-2 (2024 Compare)</span>
              </label>
              <label className="layer-option">
                <input
                  type="checkbox"
                  checked={showOverlay && activeLayers.aiPolygons}
                  onChange={(e) => {
                    setActiveLayers({ ...activeLayers, aiPolygons: e.target.checked });
                    onToggleOverlay?.(e.target.checked);
                  }}
                />
                <span style={{ color: '#ef4444', fontWeight: 600 }}>AI Change Polygons</span>
              </label>
              <label className="layer-option">
                <input
                  type="checkbox"
                  checked={activeLayers.cloudMask}
                  onChange={(e) => setActiveLayers({ ...activeLayers, cloudMask: e.target.checked })}
                />
                <span>Cloud & Shadow Mask</span>
              </label>
            </div>
          )}
        </div>

        {/* Draw tool button */}
        <button
          className={`map-stack-btn ${isDrawing ? 'btn-active' : ''}`}
          onClick={() => onToggleDrawing?.(!isDrawing)}
          title={isDrawing ? "Drawing Mode ON (Click map to annotate)" : "Annotate / Draw Area of Interest (AOI)"}
        >
          <Pencil size={15} />
        </button>

        {/* Swap button */}
        {isSplitMode && (
          <button
            className={`map-stack-btn ${isSwapped ? 'btn-active' : ''}`}
            onClick={() => setIsSwapped(!isSwapped)}
            title={`Swap Images (Currently: Left = ${isSwapped ? '2024' : '2022'}, Right = ${isSwapped ? '2022' : '2024'})`}
          >
            <ArrowLeftRight size={15} />
          </button>
        )}
      </div>

      {/* Drawing mode interactive banner */}
      {isDrawing && (
        <div className="drawing-banner">
          <Pencil size={14} />
          <span>
            {drawnPoints.length === 0
              ? 'Click anywhere on the map to pin Area of Interest corners'
              : `Point ${drawnPoints.length} placed · Click more or finish`}
          </span>
          {drawnPoints.length > 0 && (
            <button className="banner-clear-btn" onClick={handleClearDrawing} title="Clear drawn points">
              Clear
            </button>
          )}
          <button className="banner-done-btn" onClick={handleFinishDrawing}>
            Done
          </button>
        </div>
      )}

      {/* Live coordinates display (Bottom Right) */}
      <div className="coordinates">
        <span className="coord-dot" />
        Lat: {coords.lat} &nbsp;|&nbsp; Lng: {coords.lng}
      </div>
    </div>
  );
}
