export const queryPresets = {
  'Find all new buildings in this area': {
    answer: 'The analysis shows significant construction activity and expansion in the eastern part of the area between 2022 and 2024. A total of 12 new buildings and 3 large construction zones were detected, with an approximate increase of 0.42 km² in built-up area.',
    confidence: 0.91,
    task: 'Change Detection',
    metrics: [
      { title: 'New Buildings', value: '12', sub: 'Detected', icon: '🏢' },
      { title: 'Area of Change', value: '0.42 km²', sub: '↑ 18.7%', icon: '▧' },
      { title: 'Vegetation Loss', value: '6.3 ha', sub: '↓ 12.1%', icon: '🌳' },
      { title: 'Analysis Type', value: 'Change Detection', sub: 'Optical vs Optical', icon: '▱' }
    ],
    execution_trace: {
      selected_task: 'change_detection',
      tools_used: ['change_detection_tool'],
      model_used: 'EarthDial_4B_MS',
      parameters: { threshold: 0.3 }
    },
    metadata: {
      num_images: 2,
      modalities: ['Optical (Sentinel-2 L2A)', 'Optical (Sentinel-2 L2A)'],
      dates: ['15 Mar 2022', '10 Mar 2024'],
      resolution: '10m GSD',
      crs: 'EPSG:4326',
      bounds: [[30.885, 75.64], [30.915, 75.675]]
    },
    detected_areas: [
      { id: 'CHG-001', label: 'Commercial Warehouse Zone', area: '0.18 km²', confidence: '92%', type: 'Construction', lat: 30.905, lng: 75.659 },
      { id: 'CHG-002', label: 'Eastern Sector Development', area: '0.14 km²', confidence: '89%', type: 'Built-up', lat: 30.898, lng: 75.663 },
      { id: 'CHG-003', label: 'Residential Extension North', area: '0.10 km²', confidence: '85%', type: 'Residential', lat: 30.909, lng: 75.656 }
    ],
    geojson: {
      type: 'FeatureCollection',
      features: [
        { type: 'Feature', properties: { id: 'CHG-001', name: 'Commercial Warehouse Zone', change_type: 'New Construction' }, geometry: { type: 'Polygon', coordinates: [[[75.656,30.906],[75.661,30.906],[75.661,30.901],[75.656,30.901],[75.656,30.906]]] } },
        { type: 'Feature', properties: { id: 'CHG-002', name: 'Eastern Sector Development', change_type: 'Industrial Expansion' }, geometry: { type: 'Polygon', coordinates: [[[75.660,30.899],[75.666,30.899],[75.666,30.894],[75.660,30.894],[75.660,30.899]]] } },
        { type: 'Feature', properties: { id: 'CHG-003', name: 'Residential Extension North', change_type: 'New Building Cluster' }, geometry: { type: 'Polygon', coordinates: [[[75.654,30.910],[75.660,30.910],[75.660,30.906],[75.654,30.906],[75.654,30.910]]] } }
      ]
    }
  },
  'Find the new buildings and construction activity in this area between 2022 and 2024': {
    answer: 'The analysis shows significant construction activity and expansion in the eastern part of the area between 2022 and 2024. A total of 12 new buildings and 3 large construction zones were detected, with an approximate increase of 0.42 km² in built-up area.',
    confidence: 0.91,
    task: 'Change Detection',
    metrics: [
      { title: 'New Buildings', value: '12', sub: 'Detected', icon: '🏢' },
      { title: 'Area of Change', value: '0.42 km²', sub: '↑ 18.7%', icon: '▧' },
      { title: 'Vegetation Loss', value: '6.3 ha', sub: '↓ 12.1%', icon: '🌳' },
      { title: 'Analysis Type', value: 'Change Detection', sub: 'Optical vs Optical', icon: '▱' }
    ],
    execution_trace: {
      selected_task: 'change_detection',
      tools_used: ['change_detection_tool'],
      model_used: 'EarthDial_4B_MS',
      parameters: { threshold: 0.3 }
    },
    metadata: {
      num_images: 2,
      modalities: ['Optical (Sentinel-2 L2A)', 'Optical (Sentinel-2 L2A)'],
      dates: ['15 Mar 2022', '10 Mar 2024'],
      resolution: '10m GSD',
      crs: 'EPSG:4326',
      bounds: [[30.885, 75.64], [30.915, 75.675]]
    },
    detected_areas: [
      { id: 'CHG-001', label: 'Commercial Warehouse Zone', area: '0.18 km²', confidence: '92%', type: 'Construction', lat: 30.905, lng: 75.659 },
      { id: 'CHG-002', label: 'Eastern Sector Development', area: '0.14 km²', confidence: '89%', type: 'Built-up', lat: 30.898, lng: 75.663 },
      { id: 'CHG-003', label: 'Residential Extension North', area: '0.10 km²', confidence: '85%', type: 'Residential', lat: 30.909, lng: 75.656 }
    ],
    geojson: {
      type: 'FeatureCollection',
      features: [
        { type: 'Feature', properties: { id: 'CHG-001', name: 'Commercial Warehouse Zone', change_type: 'New Construction' }, geometry: { type: 'Polygon', coordinates: [[[75.656,30.906],[75.661,30.906],[75.661,30.901],[75.656,30.901],[75.656,30.906]]] } },
        { type: 'Feature', properties: { id: 'CHG-002', name: 'Eastern Sector Development', change_type: 'Industrial Expansion' }, geometry: { type: 'Polygon', coordinates: [[[75.660,30.899],[75.666,30.899],[75.666,30.894],[75.660,30.894],[75.660,30.899]]] } },
        { type: 'Feature', properties: { id: 'CHG-003', name: 'Residential Extension North', change_type: 'New Building Cluster' }, geometry: { type: 'Polygon', coordinates: [[[75.654,30.910],[75.660,30.910],[75.660,30.906],[75.654,30.906],[75.654,30.910]]] } }
      ]
    }
  },
  'Detect changes between these images': {
    answer: 'Multi-temporal EarthDial model detected 31 distinct change anomalies: 19 infrastructure expansions and 12 terrain modifications.',
    confidence: 0.91,
    task: 'Change Detection',
    metrics: [
      { title: 'Change Anomalies', value: '31', sub: 'Confirmed', icon: '⚡' },
      { title: 'Disturbed Area', value: '0.38 km²', sub: '↑ 7.8%', icon: '▧' },
      { title: 'Soil Exposure', value: '4.2 ha', sub: 'Excavation', icon: '🚜' },
      { title: 'Confidence', value: '91.0%', sub: 'Verified', icon: '✨' }
    ],
    execution_trace: {
      selected_task: 'spatiotemporal_change_detection',
      tools_used: ['spectral_angle_mapper', 'change_detector_net'],
      model_used: 'EarthDial_4B_MS',
      parameters: { threshold: 0.28 }
    },
    metadata: {
      num_images: 2,
      modalities: ['Optical Sentinel-2', 'Optical Sentinel-2'],
      dates: ['15 Mar 2022', '10 Mar 2024'],
      resolution: '10m GSD',
      crs: 'EPSG:4326',
      bounds: [[30.885, 75.64], [30.915, 75.675]]
    },
    detected_areas: [
      { id: 'CHG-101', label: 'Excavation Zone Alpha', area: '18,500 m²', confidence: '92%', type: 'Excavation', lat: 30.904, lng: 75.658 },
      { id: 'CHG-102', label: 'Highway Extension Corridor', area: '22,100 m²', confidence: '89%', type: 'Roadwork', lat: 30.897, lng: 75.662 },
      { id: 'CHG-103', label: 'Agricultural Conversion Area', area: '14,300 m²', confidence: '87%', type: 'Soil Disturbance', lat: 30.908, lng: 75.654 }
    ],
    geojson: {
      type: 'FeatureCollection',
      features: [
        { type: 'Feature', properties: { id: 'CHG-101', name: 'Excavation Zone Alpha', change_type: 'Land Clearing' }, geometry: { type: 'Polygon', coordinates: [[[75.655,30.906],[75.661,30.906],[75.661,30.900],[75.655,30.900],[75.655,30.906]]] } },
        { type: 'Feature', properties: { id: 'CHG-102', name: 'Highway Extension Corridor', change_type: 'Road Grading' }, geometry: { type: 'Polygon', coordinates: [[[75.659,30.898],[75.666,30.898],[75.666,30.893],[75.659,30.893],[75.659,30.898]]] } },
        { type: 'Feature', properties: { id: 'CHG-103', name: 'Agricultural Conversion Area', change_type: 'Soil Disturbance' }, geometry: { type: 'Polygon', coordinates: [[[75.653,30.911],[75.659,30.911],[75.659,30.905],[75.653,30.905],[75.653,30.911]]] } }
      ]
    }
  },
  'Locate roads and highlight them': {
    answer: 'Road network extraction identified 4.8 km of arterial roads and 12.2 km of feeder corridors with connected topology mapping.',
    confidence: 0.93,
    task: 'Road Grounding',
    metrics: [
      { title: 'Road Network', value: '17.0 km', sub: 'Extracted', icon: '🛣️' },
      { title: 'Paved vs Unpaved', value: '82% / 18%', sub: 'Classified', icon: '🚗' },
      { title: 'Intersections', value: '14', sub: 'Topology nodes', icon: '📍' },
      { title: 'Accuracy', value: '93.4%', sub: 'High Precision', icon: '✨' }
    ],
    execution_trace: {
      selected_task: 'road_vectorization',
      tools_used: ['road_tracer_backbone', 'graph_topology_extractor'],
      model_used: 'EarthDial_4B_MS',
      parameters: { connectivity_weight: 0.8 }
    },
    metadata: {
      num_images: 1,
      modalities: ['Optical Sentinel-2'],
      dates: ['10 Mar 2024'],
      resolution: '10m GSD',
      crs: 'EPSG:4326',
      bounds: [[30.885, 75.64], [30.915, 75.675]]
    },
    detected_areas: [
      { id: 'RD-01', label: 'Main Sector Expressway', area: '34,000 m²', confidence: '97%', type: 'Primary Road', lat: 30.902, lng: 75.659 },
      { id: 'RD-02', label: 'Agricultural Bypass Line', area: '12,500 m²', confidence: '91%', type: 'Secondary Road', lat: 30.896, lng: 75.655 }
    ],
    geojson: {
      type: 'FeatureCollection',
      features: [
        { type: 'Feature', properties: { id: 'RD-01', name: 'Main Sector Expressway', change_type: 'Paved Arterial' }, geometry: { type: 'Polygon', coordinates: [[[75.645,30.904],[75.672,30.904],[75.672,30.900],[75.645,30.900],[75.645,30.904]]] } },
        { type: 'Feature', properties: { id: 'RD-02', name: 'Agricultural Bypass Line', change_type: 'Secondary Connector' }, geometry: { type: 'Polygon', coordinates: [[[75.657,30.914],[75.661,30.914],[75.661,30.888],[75.657,30.888],[75.657,30.914]]] } }
      ]
    }
  },
  'Compare optical and SAR data': {
    answer: 'Multi-modal fusion (Optical + Sentinel-1 SAR VV/VH) identified waterlogged agricultural patches and confirmed structural backscatter signatures unaffected by cloud occlusions.',
    confidence: 0.95,
    task: 'Optical + SAR Fusion',
    metrics: [
      { title: 'SAR Backscatter', value: '-12.4 dB', sub: 'Avg VV', icon: '📡' },
      { title: 'Optical NDVI', value: '0.68', sub: 'High Biomass', icon: '🌿' },
      { title: 'Soil Moisture Ind.', value: '0.44', sub: 'Elevated SAR VH', icon: '💧' },
      { title: 'Sensor Alignment', value: 'Sub-pixel', sub: 'Co-registered', icon: '🎯' }
    ],
    execution_trace: {
      selected_task: 'multimodal_optical_sar_fusion',
      tools_used: ['radiometric_calibration', 'sar_speckle_filter', 'earthdial_fusion_head'],
      model_used: 'EarthDial_4B_MS',
      parameters: { polarizations: ['VV', 'VH'], ndvi_threshold: 0.4 }
    },
    metadata: {
      num_images: 2,
      modalities: ['Optical Sentinel-2', 'SAR Sentinel-1 (C-Band)'],
      dates: ['15 Mar 2022', '10 Mar 2024'],
      resolution: '10m GSD',
      crs: 'EPSG:4326',
      bounds: [[30.885, 75.64], [30.915, 75.675]]
    },
    detected_areas: [
      { id: 'FUS-01', label: 'SAR High Reflection Zone (Urban)', area: '26,400 m²', confidence: '96%', type: 'Urban Core', lat: 30.906, lng: 75.661 },
      { id: 'FUS-02', label: 'Moisture Retention Silt Basin', area: '15,200 m²', confidence: '93%', type: 'Water/Wetland', lat: 30.895, lng: 75.654 }
    ],
    geojson: {
      type: 'FeatureCollection',
      features: [
        { type: 'Feature', properties: { id: 'FUS-01', name: 'SAR High Reflection Zone', change_type: 'High Double-Bounce' }, geometry: { type: 'Polygon', coordinates: [[[75.657,30.908],[75.664,30.908],[75.664,30.902],[75.657,30.902],[75.657,30.908]]] } },
        { type: 'Feature', properties: { id: 'FUS-02', name: 'Moisture Basin', change_type: 'Dielectric Shift' }, geometry: { type: 'Polygon', coordinates: [[[75.651,30.898],[75.658,30.898],[75.658,30.892],[75.651,30.892],[75.651,30.898]]] } }
      ]
    }
  }
};

export const mockResult = queryPresets['Find all new buildings in this area'];

export const mockHistory = [
  { id: 1, query: 'Find the changes in this area between these two images', date: 'Today, 02:15 PM', status: 'Completed', task: 'Change Detection', confidence: '0.89' },
  { id: 2, query: 'Find all buildings in this area', date: 'Today, 01:42 PM', status: 'Completed', task: 'Building Grounding', confidence: '0.94' },
  { id: 3, query: 'Locate roads and highlight them', date: 'Yesterday, 05:20 PM', status: 'Completed', task: 'Road Grounding', confidence: '0.93' },
  { id: 4, query: 'Compare optical and SAR data', date: 'Yesterday, 11:15 AM', status: 'Completed', task: 'Optical + SAR', confidence: '0.95' },
  { id: 5, query: 'Detect flood inundation extent', date: '20 Sep 2026', status: 'Completed', task: 'VQA', confidence: '0.91' }
];

export const mockDatasets = [
  { name: 'Sentinel-2 L2A Harmonized', type: 'Optical Multispectral', bands: '13 Bands (RGB, NIR, SWIR)', resolution: '10m', source: 'ESA Copernicus', size: '2.4 GB' },
  { name: 'Sentinel-1 GRD SAR', type: 'Synthetic Aperture Radar', bands: 'VV + VH Dual-Pol', resolution: '10m', source: 'ESA Copernicus', size: '1.8 GB' },
  { name: 'Landsat-9 OLI-2 / TIRS-2', type: 'Multispectral + Thermal', bands: '11 Bands', resolution: '30m (15m Pan)', source: 'USGS / NASA', size: '1.2 GB' },
  { name: 'High-Res Aerial Orthomosaic', type: 'Optical RGB HD', bands: 'RGB True Color', resolution: '0.25m', source: 'Survey of India', size: '8.4 GB' }
];
