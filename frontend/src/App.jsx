import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ArrowUp, Bot, BrainCircuit, Link2, Loader2, Play, Search, Server, Sparkles, UploadCloud, X, Layers } from 'lucide-react';
import Sidebar from './components/layout/Sidebar';
import ResultsPanel from './components/results/ResultsPanel';
import DashboardView from './components/views/DashboardView';
import HistoryView from './components/views/HistoryView';
import DatasetsView from './components/views/DatasetsView';
import SettingsModal from './components/views/SettingsModal';
import ImageAnalysisView from './components/image/ImageAnalysisView';
import { healthCheck, postQuery } from './api/client';

const TASK_OPTIONS=[['Auto (Let AI decide)','auto'],['VQA','vqa'],['Caption','caption'],['Grounding','grounding'],['Change Detection','change'],['Optical + SAR','optical_sar'],['Metadata','metadata']];
const HISTORY_KEY='satquery.history.v1', SAVED_KEY='satquery.saved.v1';
function readStorage(key){try{const raw=localStorage.getItem(key);return raw?JSON.parse(raw):[];}catch{return[];}}
function writeStorage(key,value){try{localStorage.setItem(key,JSON.stringify(value));}catch{}}
function isGeoTiff(file){return /\.(tif|tiff|geotiff)$/i.test(file?.name||'');}
function fileLabel(file){return `${(file.size/(1024*1024)).toFixed(1)} MB · GeoTIFF`;}

function App(){
  const[activeNav,setActiveNav]=useState('Map Analysis'),[topSearch,setTopSearch]=useState(''),[query,setQuery]=useState(''),[taskHint,setTaskHint]=useState('auto'),[files,setFiles]=useState([]),[isDraggingFile,setIsDraggingFile]=useState(false);
  const[isAnalyzing,setIsAnalyzing]=useState(false),[currentResult,setCurrentResult]=useState(null),[history,setHistory]=useState(()=>readStorage(HISTORY_KEY)),[saved,setSaved]=useState(()=>readStorage(SAVED_KEY));
  const[backendOnline,setBackendOnline]=useState(false),[earthDialOnline,setEarthDialOnline]=useState(false),[omniRouteActive,setOmniRouteActive]=useState(null),[lastCheckedTime,setLastCheckedTime]=useState(''),[isSettingsOpen,setIsSettingsOpen]=useState(false),[toastMessage,setToastMessage]=useState(null);
  const[viewMode,setViewMode]=useState('Single View'),[showOverlay,setShowOverlay]=useState(true),[showToolsMenu,setShowToolsMenu]=useState(false);const fileInputRef=useRef(null);
  const showToast=useCallback(msg=>{setToastMessage(msg);window.setTimeout(()=>setToastMessage(prev=>prev===msg?null:prev),3500);},[]);
  const checkHealth=useCallback(async()=>{try{const result=await healthCheck();setBackendOnline(true);setEarthDialOnline(Boolean(result?.model?.status==='online'||result?.model?.model_loaded===true));setLastCheckedTime(new Date().toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit'}));}catch{setBackendOnline(false);setEarthDialOnline(false);}},[]);
  useEffect(()=>{checkHealth();const timer=window.setInterval(checkHealth,30000);return()=>window.clearInterval(timer);},[checkHealth]);
  useEffect(()=>{if(currentResult?.execution_trace)setOmniRouteActive(currentResult.execution_trace.router==='omniroute');},[currentResult]);
  const addFiles=useCallback(incoming=>{const geotiffs=incoming.filter(isGeoTiff);if(!geotiffs.length){showToast('Please upload GeoTIFF (.tif/.tiff/.geotiff) files for backend analysis.');return;}setFiles(prev=>{const combined=[...prev.filter(isGeoTiff),...geotiffs];if(combined.length>2)showToast('Only the latest 2 GeoTIFF files are used for backend analysis.');return combined.slice(-2);});},[showToast]);
  const analysisFiles=useMemo(()=>files.filter(isGeoTiff).slice(0,2),[files]);
  const runAnalysis=useCallback(async(queryOverride)=>{const q=(queryOverride??query??topSearch).trim();if(!q){showToast('Enter a query first.');return;}if(analysisFiles.length<1){showToast('Upload at least one GeoTIFF first.');return;}setIsAnalyzing(true);showToast('Running EarthDial on Kaggle…');try{const result=await postQuery({files:analysisFiles,query:q,taskHint:taskHint||'auto'});setCurrentResult(result);const record={id:String(Date.now()),query:q,answer:result.answer,confidence:result.confidence,task:result.execution_trace?.selected_task||'unknown',router:result.execution_trace?.router||'deterministic',timestamp:new Date().toISOString(),metadata:result.metadata||{},result};const next=[record,...history].slice(0,50);setHistory(next);writeStorage(HISTORY_KEY,next);showToast('Analysis completed successfully.');}catch(error){showToast(`${error.code?`${error.code}: `:''}${error.message}`);}finally{setIsAnalyzing(false);}},[analysisFiles,history,query,showToast,taskHint,topSearch]);
  const saveCurrentResult=()=>{if(!currentResult){showToast('Run an analysis before saving a result.');return;}const record={id:String(Date.now()),query:currentResult.report?.query||query,answer:currentResult.answer,confidence:currentResult.confidence,task:currentResult.execution_trace?.selected_task||'unknown',router:currentResult.execution_trace?.router||'deterministic',timestamp:new Date().toISOString(),metadata:currentResult.metadata||{},result:currentResult};const next=[record,...saved].slice(0,50);setSaved(next);writeStorage(SAVED_KEY,next);showToast('Result saved locally.');};
  const loadRecord=record=>{if(record?.result)setCurrentResult(record.result);if(record?.query)setQuery(record.query);setActiveNav('Map Analysis');};
  return <div className="app">
    {toastMessage&&<div className="app-toast">{toastMessage}</div>}
    <input type="file" ref={fileInputRef} onChange={e=>{addFiles(Array.from(e.target.files||[]));e.target.value='';}} multiple accept=".tif,.tiff,.geotiff" style={{display:'none'}}/>
    <SettingsModal isOpen={isSettingsOpen||activeNav==='Settings'} onClose={()=>{setIsSettingsOpen(false);if(activeNav==='Settings')setActiveNav('Map Analysis');}} onToast={showToast}/>
    <Sidebar active={activeNav} setActive={nav=>{if(nav==='Settings')setIsSettingsOpen(true);else setActiveNav(nav);}}/>
    <main className="main">
      <header className="topbar"><div className="mobile-brand">SatQuery <em>AI</em></div><form className="global-search" onSubmit={e=>{e.preventDefault();runAnalysis(topSearch);}}><Search size={19}/><input value={topSearch} onChange={e=>setTopSearch(e.target.value)} placeholder="Ask about your satellite image..."/><button type="submit" disabled={isAnalyzing}>{isAnalyzing?<Loader2 size={18} className="spinner"/>:<ArrowUp size={18}/>}</button></form><div className="top-meta">SIH 26167 <span/> Remote Sensing <div className="avatar">SIH</div></div></header>
      {activeNav==='Dashboard'&&<DashboardView latestResult={currentResult} backendOnline={backendOnline} earthDialOnline={earthDialOnline} omniRouteActive={omniRouteActive} onGoToMap={()=>setActiveNav('Map Analysis')}/>} 
      {activeNav==='Query History'&&<HistoryView isSaved={false} records={history} onLoad={loadRecord} onDelete={id=>{const next=history.filter(x=>x.id!==id);setHistory(next);writeStorage(HISTORY_KEY,next);}} onSave={record=>{const next=[record,...saved].slice(0,50);setSaved(next);writeStorage(SAVED_KEY,next);}} onGoToMap={()=>setActiveNav('Map Analysis')} onToast={showToast}/>} 
      {activeNav==='Saved Results'&&<HistoryView isSaved records={saved} onLoad={loadRecord} onDelete={id=>{const next=saved.filter(x=>x.id!==id);setSaved(next);writeStorage(SAVED_KEY,next);}} onGoToMap={()=>setActiveNav('Map Analysis')} onToast={showToast}/>} 
      {activeNav==='Datasets'&&<DatasetsView onToast={showToast} onGoToMap={()=>setActiveNav('Map Analysis')}/>} 
      {(activeNav==='Map Analysis'||activeNav==='Upload & Query')&&<>
        <div className="workspace">
          <section className="left-panel panel">
            <div className="panel-title"><h2>Upload Images</h2><UploadCloud size={18} color="#0bb27e"/></div>
            <div className={`dropzone ${isDraggingFile?'drag-over':''}`} onDragOver={e=>{e.preventDefault();setIsDraggingFile(true);}} onDragLeave={()=>setIsDraggingFile(false)} onDrop={e=>{e.preventDefault();setIsDraggingFile(false);addFiles(Array.from(e.dataTransfer.files||[]));}} onClick={()=>fileInputRef.current?.click()}><UploadCloud size={20}/><b>Drag & drop GeoTIFF files here</b><span>or</span><button type="button" onClick={e=>{e.stopPropagation();fileInputRef.current?.click();}}>Choose Files</button><small>Supported: .tif, .tiff, .geotiff · Max 2 files</small></div>
            <h4>Selected Files ({files.length})</h4>{files.map(file=><div className="file-row" key={`${file.name}-${file.lastModified}`}><div className="thumb"/><div><b>{file.name}</b><small>{fileLabel(file)}</small></div><button type="button" className="file-remove-btn" onClick={()=>setFiles(prev=>prev.filter(x=>x!==file))}><X size={14}/></button></div>)}{files.length===0&&<div className="empty-file-note">No files selected.</div>}
            <h4>Query Input</h4><textarea rows={3} value={query} maxLength={500} onChange={e=>setQuery(e.target.value)} placeholder="Ask a natural-language question about your satellite image..."/><div className="counter">{query.length}/500</div>
            <h4>Task Hint (Optional)</h4><select value={taskHint} onChange={e=>setTaskHint(e.target.value)}>{TASK_OPTIONS.map(([label,value])=><option key={value} value={value}>{label}</option>)}</select>
            <div style={{fontSize:11,color:'#64748b',margin:'6px 0 8px'}}>For image highlights, use Grounding or ask where/locate/highlight questions.</div>
            <button type="button" className="run" disabled={isAnalyzing} onClick={()=>runAnalysis()}>{isAnalyzing?<><Loader2 size={15} className="spinner"/> Analyzing…</>:<><Play size={15} fill="currentColor"/> Run Analysis</>}</button>
            <h4>Sample Queries</h4>{['Where are the built-up areas? Highlight them.','Locate water bodies in this image and mark them.','Find agricultural fields and show their regions.','Highlight roads visible in this satellite image.','Describe what is visible in this satellite image.','What is the CRS, image size, and number of bands?','Compare these two satellite images and identify the major changes.','Analyze the optical and SAR images together.'].map(sample=><button type="button" className={`sample ${query===sample?'active-sample':''}`} key={sample} onClick={()=>{setQuery(sample);runAnalysis(sample);}}><Sparkles size={13}/><span>{sample}</span></button>)}
          </section>
          <section className="center-panel">
            <div className="view-tabs">{['Split View','Single View','Swipe','Side by Side'].map(mode=><button key={mode} className={viewMode===mode?'active':''} onClick={()=>setViewMode(mode)}>{mode}</button>)}<div className="grow"/><button className={showToolsMenu?'active':''} onClick={()=>setShowToolsMenu(v=>!v)}><Layers size={14}/> Tools ⌄</button>{showToolsMenu&&<div className="tools-dropdown-menu"><button onClick={()=>{setShowOverlay(v=>!v);setShowToolsMenu(false);}}>{showOverlay?'Hide AI Overlays':'Show AI Overlays'}</button><button onClick={()=>{setShowToolsMenu(false);showToast('Manual AOI remains available in the secondary Geo view.');}}>Annotate Region</button></div>}</div>
            <ImageAnalysisView files={analysisFiles} resultData={currentResult} viewMode={viewMode} showOverlay={showOverlay}/>
            <div className="metrics"><Metric title="Images" value={currentResult?.metadata?.num_images??analysisFiles.length} sub="Uploaded" icon="▧"/><Metric title="Task" value={currentResult?.execution_trace?.selected_task??'—'} sub="Backend selected" icon="⌘"/><Metric title="Confidence" value={currentResult?`${Math.round((currentResult.confidence||0)*100)}%`:'—'} sub="Backend response" icon="✓"/><Metric title="CRS" value={currentResult?.metadata?.crs??'—'} sub="GeoTIFF metadata" icon="⌖"/></div>
          </section>
          <ResultsPanel result={currentResult} onFocusArea={()=>{}} onToast={showToast} onSave={saveCurrentResult} backendOnline={backendOnline}/>
        </div>
        <StatusBar backendOnline={backendOnline} earthDialOnline={earthDialOnline} omniRouteActive={omniRouteActive} lastChecked={lastCheckedTime} onRefresh={checkHealth}/>
      </>}
    </main>
  </div>;
}
function Metric({title,value,sub,icon}){return <div className="metric"><span className="metric-icon">{icon}</span><div><span>{title}</span><b>{String(value)}</b><small>{sub}</small></div></div>}
function StatusBar({backendOnline,earthDialOnline,omniRouteActive,lastChecked,onRefresh}){return <footer className="statusbar"><Status icon={<Server size={20}/>} label="Backend" value={backendOnline?'Connected':'Offline'} good={backendOnline}/><Status icon={<Bot size={20}/>} label="Model" value={earthDialOnline?'EarthDial_4B_MS':'Unavailable'} good={earthDialOnline}/><Status icon={<BrainCircuit size={20}/>} label="LoRA" value="OFF"/><Status icon={<Link2 size={20}/>} label="OmniRoute" value={omniRouteActive===true?'Active':omniRouteActive===false?'Fallback':'Unknown'} good={omniRouteActive===true}/><div className="checked" onClick={onRefresh} style={{cursor:'pointer'}}>↻ Last Checked: {lastChecked||'—'}</div></footer>}
function Status({icon,label,value,good}){return <div className="status-item">{icon}<div><b>{label}</b><span className={good?'good':''}>{good&&<i/>}{value}</span></div></div>}
export default App;
