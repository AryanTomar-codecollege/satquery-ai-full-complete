import { useEffect, useMemo, useState } from 'react';
import { Image as ImageIcon, Loader2 } from 'lucide-react';
import { postPreview } from '../../api/client';

function featureBoxes(result){
  return (result?.geojson?.features||[]).filter(f=>Array.isArray(f?.properties?.bbox_pixel)&&f.properties.bbox_pixel.length===4).map((f,i)=>({id:i,label:f.properties.label||f.properties.name||'Detected feature',bbox:f.properties.bbox_pixel}));
}
function PreviewPane({file,preview,width,height,boxes,showOverlay,label}){
  if(!file)return <div style={styles.empty}><ImageIcon size={30}/><span>Upload a GeoTIFF to inspect</span></div>;
  return <div style={styles.pane}>
    {preview?<img src={preview} alt={file.name} style={styles.image}/>:<div style={styles.loading}><Loader2 size={24} className="spinner"/><span>Creating satellite preview…</span></div>}
    {showOverlay&&preview&&boxes.map(box=>{const[x1,y1,x2,y2]=box.bbox;const left=Math.max(0,Math.min(100,x1/width*100));const top=Math.max(0,Math.min(100,y1/height*100));const w=Math.max(0,Math.min(100-left,(x2-x1)/width*100));const h=Math.max(0,Math.min(100-top,(y2-y1)/height*100));return <div key={box.id} style={{...styles.box,left:`${left}%`,top:`${top}%`,width:`${w}%`,height:`${h}%`}}><span style={styles.label}>{box.label}</span></div>})}
    <div style={styles.badge}>{label||file.name}</div>
  </div>;
}
export default function ImageAnalysisView({files=[],resultData,viewMode='Single View',showOverlay=true}){
  const[previews,setPreviews]=useState([]);const[active,setActive]=useState(0);const[error,setError]=useState('');
  const dims=resultData?.metadata?.image_dimensions||[];
  useEffect(()=>{let alive=true;const urls=[];async function load(){setError('');const next=[];for(const file of files.slice(0,2)){try{const url=await postPreview(file);urls.push(url);next.push(url);}catch(e){next.push(null);if(alive)setError(e.message);}}if(alive)setPreviews(next);}setPreviews([]);load();return()=>{alive=false;urls.forEach(URL.revokeObjectURL);};},[files]);
  const boxes=useMemo(()=>featureBoxes(resultData),[resultData]);
  const showTwo=files.length>1&&(viewMode==='Split View'||viewMode==='Side by Side'||viewMode==='Swipe');
  return <div style={styles.shell}>
    <div style={styles.toolbar}><div><b>Image Analysis View</b><small>Real uploaded GeoTIFF preview · EarthDial evidence overlays</small></div><div style={styles.controls}>{files.length>1&&files.map((f,i)=><button key={f.name+i} onClick={()=>setActive(i)} style={active===i?styles.activeBtn:styles.btn}>Image {i+1}</button>)}<span style={styles.evidence}>{boxes.length} highlight{boxes.length===1?'':'s'}</span></div></div>
    {error&&<div style={styles.notice}>{error}</div>}
    {showTwo?<div style={styles.grid}>{files.slice(0,2).map((file,i)=>{const d=dims[i]||{width:1,height:1};return <PreviewPane key={file.name+i} file={file} preview={previews[i]} width={d.width} height={d.height} boxes={boxes} showOverlay={showOverlay} label={`Image ${i+1} · ${file.name}`}/>})}</div>:<PreviewPane file={files[active]} preview={previews[active]} width={(dims[active]||{}).width||1} height={(dims[active]||{}).height||1} boxes={boxes} showOverlay={showOverlay} label={files[active]?.name}/>} 
    {files.length>0&&<div style={styles.footer}>{resultData?.geojson?.features?.length?'AI location evidence is drawn from backend pixel bbox properties.':resultData?'No location boxes returned.':'File uploaded — run an analysis to request location evidence.'}</div>}
  </div>;
}
const styles={shell:{height:'100%',minHeight:420,background:'#111827',borderRadius:12,overflow:'hidden',display:'flex',flexDirection:'column',border:'1px solid rgba(255,255,255,.08)'},toolbar:{padding:'10px 12px',display:'flex',justifyContent:'space-between',alignItems:'center',gap:12,color:'#fff',background:'#0f172a'},controls:{display:'flex',alignItems:'center',gap:6,flexWrap:'wrap'},btn:{border:'1px solid #334155',background:'#1e293b',color:'#cbd5e1',borderRadius:6,padding:'5px 8px',fontSize:11},activeBtn:{border:'1px solid #0bb27e',background:'#12352e',color:'#fff',borderRadius:6,padding:'5px 8px',fontSize:11},evidence:{fontSize:11,color:'#a7f3d0',padding:'5px 8px'},pane:{position:'relative',flex:1,minHeight:0,overflow:'hidden',background:'#020617'},image:{display:'block',width:'100%',height:'100%',objectFit:'contain',background:'#020617'},loading:{height:'100%',minHeight:420,display:'flex',alignItems:'center',justifyContent:'center',gap:8,color:'#cbd5e1'},empty:{height:'100%',minHeight:420,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',gap:10,color:'#94a3b8'},box:{position:'absolute',border:'2px solid #ef4444',background:'rgba(239,68,68,.18)',boxSizing:'border-box',pointerEvents:'none'},label:{position:'absolute',top:-20,left:-2,background:'#ef4444',color:'#fff',fontSize:10,padding:'2px 4px',whiteSpace:'nowrap'},notice:{padding:'7px 12px',background:'#3f2a10',color:'#fed7aa',fontSize:11},badge:{position:'absolute',top:10,left:10,padding:'5px 8px',borderRadius:6,background:'rgba(15,23,42,.8)',color:'#fff',fontSize:11,maxWidth:'70%',whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'},footer:{padding:'8px 12px',fontSize:11,color:'#94a3b8',background:'#0f172a'},grid:{display:'grid',gridTemplateColumns:'1fr 1fr',gap:2,flex:1,minHeight:0}}
