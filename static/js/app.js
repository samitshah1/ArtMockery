const $ = id => document.getElementById(id);
const defaults = {preset:"warm_plaster",scene:"wall",wallColor:"#d8cbb8",tint:12,texture:45,frame:"oak",frameColor:"#c7a274",frameHighlightColor:"#e1c59b",frameShadowColor:"#a98456",matColor:"#f4f0e7",frameWidth:4,matWidth:8,artZoom:100,artWidth:100,artHeight:100,shadow:35,outW:2400,outH:2400,format:"PNG",orientation:"portrait",artX:0,artY:0};
let paintingImg = null, wallImg = null, paintingFile = null, wallFile = null, previewTimer = null;
const colors = {warm_plaster:"#d8cbb8",white_stucco:"#e9e7df",limewash:"#d9d0c0",travertine:"#d3c1a5",limestone:"#d5cbb8",sandstone:"#c9b18f",clay:"#bd8064",grasscloth:"#cabb9e",linen:"#ddd5c8",wood_slats:"#bd9568",brick:"#b8785e",marble:"#dfdcd4",microcement:"#bdbbb4",concrete:"#aaa9a3",sage:"#a5b09b",greige:"#c1bbb0"};
const controls = ["wallColor","tint","texture","frame","frameColor","frameHighlightColor","frameShadowColor","matColor","orientation","frameWidth","matWidth","artZoom","artWidth","artHeight","artX","artY","shadow","outW","outH","format"];
function settings(){return {preset:document.querySelector(".preset.active")?.dataset.preset||"warm_plaster",scene:"wall",wallColor:$("wallColor").value,tint:+$("tint").value,texture:+$("texture").value,frame:$("frame").value,orientation:$("orientation").value,frameColor:$("frameColor").value,frameHighlightColor:$("frameHighlightColor").value,frameShadowColor:$("frameShadowColor").value,matColor:$("matColor").value,frameWidth:+$("frameWidth").value,matWidth:+$("matWidth").value,artZoom:+$("artZoom").value,artWidth:+$("artWidth").value,artHeight:+$("artHeight").value,artX:+$("artX").value,artY:+$("artY").value,shadow:+$("shadow").value,outW:clamp(+ $("outW").value||2400,800,6000),outH:clamp(+ $("outH").value||2400,800,6000),format:$("format").value};}
function clamp(v,a,b){return Math.max(a,Math.min(b,v))}
function updateLabels(){["tint","texture","frameWidth","matWidth","artZoom","artWidth","artHeight","shadow"].forEach(k=>$(k+"Val").textContent=$(k).value+"%");["artX","artY"].forEach(k=>$(k+"Val").textContent=(+$(k).value>0?"+":"")+$(k).value+"%")}
function loadImage(file){return new Promise((resolve,reject)=>{const url=URL.createObjectURL(file),img=new Image();img.onload=()=>{URL.revokeObjectURL(url);resolve(img)};img.onerror=reject;img.src=url})}
function roundRect(ctx,x,y,w,h,r){ctx.beginPath();ctx.roundRect(x,y,w,h,r)}
function seededNoise(ctx,w,h,alpha){const im=ctx.createImageData(w,h);let seed=81273;for(let i=0;i<im.data.length;i+=4){seed=(seed*1664525+1013904223)>>>0;const n=((seed>>>24)-128)*alpha/100;im.data[i]=128+n;im.data[i+1]=128+n;im.data[i+2]=128+n;im.data[i+3]=Math.min(75,Math.abs(n)*2)}ctx.putImageData(im,0,0)}
function drawPresetWall(ctx,W,H,opts){
 const p=opts.preset||"warm_plaster",base=opts.wallColor;
 ctx.fillStyle=base;ctx.fillRect(0,0,W,H);
 const strength=opts.texture/100; if(strength<=0)return;
 const line=(color,alpha,width,x1,y1,x2,y2)=>{ctx.globalAlpha=alpha;ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();ctx.globalAlpha=1};
 if(p==="wood_slats"){
   for(let x=0;x<W;x+=Math.max(16,W/28)){line("#735437",.35*strength,Math.max(2,W/350),x,0,x,H);line("#f2d4a8",.25*strength,Math.max(1,W/500),x+Math.max(4,W/180),0,x+Math.max(4,W/180),H);for(let y=30;y<H;y+=90)line("#805d3b",.12*strength,1,x+3,y,x+Math.max(5,W/180),y+25)}
 }else if(p==="grasscloth"||p==="linen"){
   const step=Math.max(3,Math.round(Math.min(W,H)/(p==="linen"?150:95)));
   for(let y=0;y<H;y+=step){line(y%2?"#fff4df":"#77664f",.20*strength,1,0,y,W,y)}
   for(let x=0;x<W;x+=step){line(x%2?"#fff4df":"#77664f",.18*strength,1,x,0,x,H)}
 }else if(p==="brick"){
   const bh=Math.max(24,H/18),bw=Math.max(42,W/10);
   for(let y=0;y<H;y+=bh){line("#e5d4c4",.85,Math.max(2,bh*.07),0,y,W,y);const off=(Math.round(y/bh)%2)*bw/2;for(let x=-off;x<W;x+=bw)line("#e5d4c4",.8,Math.max(2,bw*.035),x,y,x,y+bh)}
 }else if(p==="travertine"){
   for(let y=H*.08;y<H;y+=Math.max(15,H/24)){line("#8d775c",.16*strength,Math.max(1,H/500),0,y,W,y+Math.sin(y/60)*H*.006);line("#fff1d7",.25*strength,Math.max(1,H/600),0,y+3,W,y+3)}
 }else if(p==="marble"){
   for(let i=0;i<9;i++){let x=(i*137%101)/100*W,y=(i*83%97)/100*H;ctx.beginPath();ctx.moveTo(x,y);ctx.bezierCurveTo(x+W*.07,y-H*.08,x-W*.08,y+H*.1,x+W*.12,y+H*.2);ctx.strokeStyle=i%2?"#ffffff":"#89877f";ctx.globalAlpha=(i%2?.22:.12)*strength;ctx.lineWidth=Math.max(1,W/450);ctx.stroke();ctx.globalAlpha=1}
 }else if(p==="limestone"||p==="microcement"||p==="concrete"){
   for(let i=0;i<100;i++){const x=(i*173%997)/997*W,y=(i*293%991)/991*H,r=(i%4+1)*Math.max(1,W/1500);ctx.fillStyle=i%2?"#ffffff":"#6d6a61";ctx.globalAlpha=(i%2?.13:.08)*strength;ctx.beginPath();ctx.ellipse(x,y,r*2,r,0,0,Math.PI*2);ctx.fill();ctx.globalAlpha=1}
 }else if(p==="limewash"||p==="warm_plaster"||p==="white_stucco"||p==="sandstone"||p==="clay"||p==="sage"||p==="greige"){
   for(let i=0;i<Math.round(110*strength);i++){const x=(i*197%991)/991*W,y=(i*313%983)/983*H;ctx.beginPath();ctx.ellipse(x,y,W*.025,H*.012,(i%7)*.2,0,Math.PI*2);ctx.fillStyle=i%2?"#fff9ed":"#776b5d";ctx.globalAlpha=(p==="limewash"?.09:.055)*strength;ctx.fill();ctx.globalAlpha=1}
 }
 // Fine natural grain keeps every material from looking digitally flat.
 const off=document.createElement("canvas");off.width=Math.min(W,500);off.height=Math.min(H,500);seededNoise(off.getContext("2d"),off.width,off.height,opts.texture);ctx.globalAlpha=.12*strength;ctx.drawImage(off,0,0,W,H);ctx.globalAlpha=1;
}
function drawRoomForeground(ctx,W,H,scene){
 if(!scene||scene==="wall")return;
 const floorY=H*.78, scale=W/900;
 const rect=(x,y,w,h,c)=>{ctx.fillStyle=c;ctx.fillRect(x,y,w,h)};
 const rr=(x,y,w,h,r,c)=>{ctx.fillStyle=c;roundRect(ctx,x,y,w,h,r);ctx.fill()};
 const ellipse=(x,y,rx,ry,c)=>{ctx.fillStyle=c;ctx.beginPath();ctx.ellipse(x,y,rx,ry,0,0,Math.PI*2);ctx.fill()};
 const line=(x1,y1,x2,y2,c,l=2)=>{ctx.strokeStyle=c;ctx.lineWidth=l;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke()};
 // Floor, skirting and understated plank seams
 const floors={living:"#b99570",bedroom:"#c4aa8a",japandi:"#c9b99e",modern_bedroom:"#9f8a75"};
 rect(0,floorY,W,H-floorY,floors[scene]||"#b99570");rect(0,floorY-5*scale,W,7*scale,"#f0e9dc");
 for(let i=0;i<8;i++){const yy=floorY+(i+1)*(H-floorY)/9;line(0,yy,W,yy,"#6f563d",Math.max(1,scale));}
 for(let x=-W;x<W*2;x+=W*.22){line(x,floorY,x+W*.13,H,"#795f45",Math.max(1,scale*.8));}
 // Rug
 if(scene!=="modern_bedroom"){rr(W*.23,H*.84,W*.54,H*.17,Math.max(8,18*scale),scene==="japandi"?"#e4ded1":"#e6d9c5");rr(W*.27,H*.865,W*.46,H*.12,Math.max(6,12*scale),scene==="japandi"?"#d4cbb9":"#d7c3a9");}
 if(scene==="living"||scene==="japandi"){
   // Sofa, seat, arms, cushions and feet
   const sofa=scene==="japandi"?"#b9b09f":"#8f9a88", cushion=scene==="japandi"?"#d9d2c5":"#c9c5b7";
   rect(W*.18,H*.73,W*.64,H*.12,sofa);rr(W*.15,H*.67,W*.70,H*.15,18*scale,sofa);rr(W*.21,H*.65,W*.58,H*.13,12*scale,sofa);
   rr(W*.25,H*.66,W*.17,H*.11,10*scale,cushion);rr(W*.44,H*.66,W*.16,H*.11,10*scale,scene==="japandi"?"#9caa98":"#d6c1a6");rr(W*.61,H*.66,W*.15,H*.11,10*scale,cushion);
   rect(W*.21,H*.81,W*.025,H*.06,"#614b37");rect(W*.76,H*.81,W*.025,H*.06,"#614b37");
   // Side table and lamp
   ellipse(W*.12,H*.79,W*.07*1.2,H*.012,"#775b3d");rect(W*.115,H*.79,W*.01,H*.08,"#76583b");ellipse(W*.12,H*.87,W*.05,H*.012,"#76583b");
   rect(W*.105,H*.66,W*.03,H*.08,"#e7dfcf");ctx.beginPath();ctx.moveTo(W*.08,H*.67);ctx.lineTo(W*.16,H*.67);ctx.lineTo(W*.145,H*.61);ctx.lineTo(W*.095,H*.61);ctx.closePath();ctx.fillStyle="#e8d9b9";ctx.fill();
   // plant at far right
   rect(W*.88,H*.75,W*.055,H*.10,"#b67f5c");ellipse(W*.907,H*.75,W*.04,H*.012,"#c58f6b");
   for(let i=0;i<7;i++){const x=W*(.905+(i%3-1)*.035),y=H*(.74-Math.floor(i/3)*.035);line(W*.907,H*.75,x,y,"#526b4f",2*scale);ellipse(x,y,W*.018,H*.035,"#71896b");}
 }else{
   // Bed with headboard, layered duvet, pillows, bedside tables and lamps
   rect(W*.16,H*.57,W*.68,H*.21,scene==="modern_bedroom"?"#75685e":"#b8a58f");
   rr(W*.13,H*.66,W*.74,H*.20,12*scale,scene==="modern_bedroom"?"#ded9d0":"#eee7dc");
   rr(W*.16,H*.65,W*.68,H*.16,10*scale,scene==="modern_bedroom"?"#aeb9b4":"#d7d4c9");
   rr(W*.22,H*.65,W*.22,H*.07,8*scale,"#f4efe6");rr(W*.47,H*.65,W*.22,H*.07,8*scale,"#f4efe6");
   // blanket folded across foot of bed
   rr(W*.16,H*.77,W*.68,H*.07,8*scale,scene==="modern_bedroom"?"#899a97":"#b7bfae");
   rect(W*.07,H*.72,W*.09,H*.10,"#8b6a4b");rect(W*.84,H*.72,W*.09,H*.10,"#8b6a4b");
   rect(W*.095,H*.63,W*.04,H*.09,"#e8ddc8");ctx.beginPath();ctx.moveTo(W*.07,H*.64);ctx.lineTo(W*.16,H*.64);ctx.lineTo(W*.145,H*.58);ctx.lineTo(W*.085,H*.58);ctx.closePath();ctx.fillStyle="#e8ddc8";ctx.fill();
   rect(W*.86,H*.63,W*.04,H*.09,"#e8ddc8");ctx.beginPath();ctx.moveTo(W*.835,H*.64);ctx.lineTo(W*.925,H*.64);ctx.lineTo(W*.91,H*.58);ctx.lineTo(W*.85,H*.58);ctx.closePath();ctx.fillStyle="#e8ddc8";ctx.fill();
 }
 // Soft daylight window on the left upper wall, only outside the artwork's center
 if(scene==="living"||scene==="modern_bedroom"){
   rr(W*.035,H*.10,W*.12,H*.30,4*scale,"#f6f0e5");rect(W*.047,H*.115,W*.096,H*.27,"#c7d6d8");rect(W*.091,H*.115,W*.006,H*.27,"#f7f0e5");rect(W*.047,H*.245,W*.096,H*.006,"#f7f0e5");
 }
}

function previewSceneQuad(W,H,scene,aspect){
 const profiles={living:[.50,.345,.355,.445,.008,-.004,-.010,.012],bedroom:[.505,.305,.325,.405,-.004,.004,.002,-.002],japandi:[.525,.335,.335,.425,.018,-.018,-.012,.026],modern_bedroom:[.465,.315,.325,.405,-.020,.012,.012,-.030]};
 const [cx,cy,mw,mh,tl,tr,bl,br]=profiles[scene]||profiles.living;
 let w=Math.min(W*mw,H*mh*aspect),h=w/Math.max(aspect,.15);if(h>H*mh){h=H*mh;w=h*aspect;}
 const x1=cx*W-w/2,x2=cx*W+w/2,y1=cy*H-h/2,y2=cy*H+h/2;
 return [[x1+tl*W,y1],[x2+tr*W,y1+H*.004],[x2+br*W,y2],[x1+bl*W,y2-H*.002]];
}
function drawPerspectiveImage(ctx,img,quad,steps=14){
 const [tl,tr,br,bl]=quad;
 const point=(u,v)=>[(1-u)*(1-v)*tl[0]+u*(1-v)*tr[0]+u*v*br[0]+(1-u)*v*bl[0],(1-u)*(1-v)*tl[1]+u*(1-v)*tr[1]+u*v*br[1]+(1-u)*v*bl[1]];
 function triangle(src,dst){
   const [p0,p1,p2]=src,[q0,q1,q2]=dst;const den=(p1[0]-p0[0])*(p2[1]-p0[1])-(p2[0]-p0[0])*(p1[1]-p0[1]);if(Math.abs(den)<1e-8)return;
   const a=((q1[0]-q0[0])*(p2[1]-p0[1])-(q2[0]-q0[0])*(p1[1]-p0[1]))/den;
   const c=((p1[0]-p0[0])*(q2[0]-q0[0])-(p2[0]-p0[0])*(q1[0]-q0[0]))/den;
   const b=((q1[1]-q0[1])*(p2[1]-p0[1])-(q2[1]-q0[1])*(p1[1]-p0[1]))/den;
   const d=((p1[0]-p0[0])*(q2[1]-q0[1])-(p2[0]-p0[0])*(q1[1]-q0[1]))/den;
   const e=q0[0]-a*p0[0]-c*p0[1],f=q0[1]-b*p0[0]-d*p0[1];
   ctx.save();ctx.beginPath();ctx.moveTo(q0[0],q0[1]);ctx.lineTo(q1[0],q1[1]);ctx.lineTo(q2[0],q2[1]);ctx.closePath();ctx.clip();ctx.setTransform(a,b,c,d,e,f);ctx.drawImage(img,0,0);ctx.restore();
 }
 for(let y=0;y<steps;y++)for(let x=0;x<steps;x++){
   const u0=x/steps,u1=(x+1)/steps,v0=y/steps,v1=(y+1)/steps;
   const sx0=u0*img.width,sx1=u1*img.width,sy0=v0*img.height,sy1=v1*img.height;
   const p00=point(u0,v0),p10=point(u1,v0),p11=point(u1,v1),p01=point(u0,v1);
   triangle([[sx0,sy0],[sx1,sy0],[sx1,sy1]],[p00,p10,p11]);triangle([[sx0,sy0],[sx1,sy1],[sx0,sy1]],[p00,p11,p01]);
 }
}
function drawMockup(canvas, opts, final=false){
 const mainCtx=canvas.getContext("2d"), W=canvas.width,H=canvas.height;
 mainCtx.clearRect(0,0,W,H);
 // Real photographic room scenes; wall view retains the original customizable wall.
 const roomPhoto=opts.scene&&opts.scene!=="wall"?roomImages[opts.scene]:null;
 if(roomPhoto){const scale=Math.max(W/roomPhoto.width,H/roomPhoto.height),sw=W/scale,sh=H/scale;mainCtx.drawImage(roomPhoto,(roomPhoto.width-sw)/2,(roomPhoto.height-sh)/2,sw,sh,0,0,W,H)}
 else if(wallImg){const scale=Math.max(W/wallImg.width,H/wallImg.height),sw=W/scale,sh=H/scale;mainCtx.drawImage(wallImg,(wallImg.width-sw)/2,(wallImg.height-sh)/2,sw,sh,0,0,W,H)}
 else {drawPresetWall(mainCtx,W,H,opts)}
 // Wall controls apply only to the default wall view or a user-supplied wall photo.
 if(!roomPhoto && wallImg && opts.tint>0){mainCtx.globalAlpha=opts.tint/100;mainCtx.fillStyle=opts.wallColor;mainCtx.fillRect(0,0,W,H);mainCtx.globalAlpha=1}
 if(!roomPhoto && wallImg && opts.texture>0){const off=document.createElement("canvas");off.width=Math.min(W,1000);off.height=Math.min(H,1000);seededNoise(off.getContext("2d"),off.width,off.height,opts.texture);mainCtx.globalAlpha=opts.texture/190;mainCtx.drawImage(off,0,0,W,H);mainCtx.globalAlpha=1}
 const roomScene=opts.scene&&opts.scene!=="wall";
 const artLayer=roomScene?document.createElement("canvas"):canvas;
 if(roomScene){artLayer.width=W;artLayer.height=H;}
 const ctx=artLayer.getContext("2d");if(roomScene)ctx.clearRect(0,0,W,H);
 // composition size leaves comfortable wall margin
 const maxW=W*(roomScene?.34:.59),maxH=H*(roomScene?.43:.68);let aw=paintingImg?paintingImg.width:3,ah=paintingImg?paintingImg.height:4;
 const ratio=opts.orientation==="landscape"?(4/3):(3/4);let innerW=Math.min(maxW,maxH*ratio),innerH=innerW/ratio;innerW*=clamp((opts.artWidth||100)/100,.25,1.5);innerH*=clamp((opts.artHeight||100)/100,.25,1.5);
 const fw=opts.frame==="canvas"?0:Math.max(2,Math.round(Math.min(W,H)*opts.frameWidth/100));
 const mat=opts.frame==="canvas"?0:Math.round(Math.min(innerW,innerH)*opts.matWidth/100);
 const totalW=innerW+2*(fw+mat),totalH=innerH+2*(fw+mat);
 const x=(W-totalW)/2 + W*(opts.artX||0)/100,y=(opts.scene&&opts.scene!=="wall"?Math.max(H*.045,(H*.64-totalH)/2):(H-totalH)/2) + H*(opts.artY||0)/100;
 // soft shadow
 if(opts.shadow>0&&opts.frame!=="canvas"){
   ctx.save();ctx.shadowColor=`rgba(0,0,0,${opts.shadow/240})`;ctx.shadowBlur=Math.min(W,H)*.025;ctx.shadowOffsetX=Math.min(W,H)*.004;ctx.shadowOffsetY=Math.min(W,H)*.012;ctx.fillStyle="#fff";ctx.fillRect(x,y,totalW,totalH);ctx.restore();
 }
 const finishes={black:["#242321","#4c4a46","#171716"],white:["#eeeae1","#ffffff","#cbc7bf"],oak:["#c7a274","#e1c59b","#a98456"],walnut:["#69462f","#8a6142","#493021"],gold:["#b49a5e","#e0cb8b","#8f743d"]};
 const mixHex=(hex,amount)=>{const n=parseInt((hex||"#c7a274").replace("#",""),16);return "#"+[16,8,0].map(sh=>{const c=(n>>sh)&255;const v=amount>=0?c*(1-amount)+255*amount:c*(1+amount);return Math.round(Math.max(0,Math.min(255,v))).toString(16).padStart(2,"0")}).join("")};
 if(opts.frame!=="canvas"){
   const base=opts.frame==="custom"?[opts.frameColor||"#c7a274",mixHex(opts.frameColor||"#c7a274",.3),mixHex(opts.frameColor||"#c7a274",-.3)]: (finishes[opts.frame]||finishes.oak);
   const f=[base[0],opts.frameHighlightColor||base[1],opts.frameShadowColor||base[2]];
   ctx.fillStyle=f[0];ctx.fillRect(x,y,totalW,totalH);
   const bands=Math.max(1,Math.round(fw/3));
   for(let i=0;i<bands;i++){ctx.strokeStyle=i%2?f[1]:f[2];ctx.lineWidth=1;ctx.strokeRect(x+i,y+i,totalW-2*i,totalH-2*i)}
   // inner bevel highlight
   ctx.fillStyle=f[2];ctx.fillRect(x+fw,y+fw,totalW-2*fw,totalH-2*fw);
   if(mat>0){ctx.fillStyle=opts.matColor||"#f4f0e7";ctx.fillRect(x+fw,y+fw,totalW-2*fw,totalH-2*fw)}
 }
 const ix=x+fw+mat,iy=y+fw+mat;
 ctx.fillStyle="#f8f7f2";ctx.fillRect(ix,iy,innerW,innerH);
 if(paintingImg){
   // Keep the frame opening fixed; zoom crops or reveals the artwork within it.
   const zoom=clamp((opts.artZoom||100)/100,.7,2);
   const sc=Math.min(innerW/paintingImg.width,innerH/paintingImg.height)*zoom;
   const pw=paintingImg.width*sc,ph=paintingImg.height*sc;
   ctx.save();ctx.beginPath();ctx.rect(ix,iy,innerW,innerH);ctx.clip();
   ctx.drawImage(paintingImg,ix+(innerW-pw)/2,iy+(innerH-ph)/2,pw,ph);ctx.restore();
 } else {
   ctx.fillStyle="#e7e2d8";ctx.fillRect(ix,iy,innerW,innerH);
   ctx.fillStyle="#77736b";ctx.textAlign="center";ctx.textBaseline="middle";ctx.font=`${Math.max(12,W*.018)}px sans-serif`;ctx.fillText("Upload your painting",ix+innerW/2,iy+innerH/2);
 }
 // Inner frame edge
 if(opts.frame!=="canvas"&&fw>0){ctx.strokeStyle="rgba(0,0,0,.28)";ctx.lineWidth=Math.max(1,fw*.08);ctx.strokeRect(ix-1,iy-1,innerW+2,innerH+2)}
 if(roomScene){
   const crop=document.createElement("canvas");crop.width=Math.max(1,Math.round(totalW));crop.height=Math.max(1,Math.round(totalH));
   crop.getContext("2d").drawImage(artLayer,x,y,totalW,totalH,0,0,crop.width,crop.height);
   const quad=previewSceneQuad(W,H,opts.scene,crop.width/crop.height);
   drawPerspectiveImage(mainCtx,crop,quad,14);
 }
}
function schedulePreview(){clearTimeout(previewTimer);previewTimer=setTimeout(()=>{drawMockup($("preview"),settings());},80)}
function setPreset(p){document.querySelectorAll(".preset").forEach(b=>b.classList.toggle("active",b.dataset.preset===p));if(colors[p])$("wallColor").value=colors[p];schedulePreview()}
document.querySelectorAll(".preset").forEach(b=>b.addEventListener("click",()=>{wallImg=null;wallFile=null;$("wallphoto").value="";setPreset(b.dataset.preset)}));
$("frameColor").addEventListener("input",()=>{$("frame").value="custom";updateLabels();schedulePreview()});
$("frame").addEventListener("change",()=>{const presets={black:"#242321",white:"#eeeae1",oak:"#c7a274",walnut:"#69462f",gold:"#b49a5e"};if(presets[$("frame").value])$("frameColor").value=presets[$("frame").value];updateLabels();schedulePreview()});
controls.forEach(k=>$(k).addEventListener("input",()=>{updateLabels();schedulePreview()}));
$("previewZoom").addEventListener("input",()=>{const z=+$("previewZoom").value;$("previewZoomVal").textContent=z+"%";$("preview").style.setProperty("--preview-zoom",z/100);if(z<=100){previewPanX=0;previewPanY=0;applyPreviewPan();}else preview.classList.add("is-zoomed");});
const preview=$("preview");let previewPanX=0,previewPanY=0,dragStart=null;
function applyPreviewPan(){preview.style.setProperty("--preview-x",previewPanX+"px");preview.style.setProperty("--preview-y",previewPanY+"px");const zoom=+$("previewZoom").value;preview.classList.toggle("is-zoomed",zoom>100);}
preview.addEventListener("pointerdown",e=>{if(+$("previewZoom").value<=100)return;dragStart={x:e.clientX,y:e.clientY,panX:previewPanX,panY:previewPanY};preview.classList.add("is-dragging");preview.setPointerCapture(e.pointerId);e.preventDefault();});
preview.addEventListener("pointermove",e=>{if(!dragStart)return;previewPanX=dragStart.panX+e.clientX-dragStart.x;previewPanY=dragStart.panY+e.clientY-dragStart.y;applyPreviewPan();});
function stopPreviewDrag(){dragStart=null;preview.classList.remove("is-dragging");}
preview.addEventListener("pointerup",stopPreviewDrag);preview.addEventListener("pointercancel",stopPreviewDrag);

// Reusable configuration files contain settings and, when applicable, the uploaded wall photo.
// The painting itself is deliberately excluded so one setup can be reused for many artworks.
function fileToDataURL(file){
 return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=()=>reject(new Error("Could not read the wall photo."));reader.readAsDataURL(file)})
}
async function dataURLToFile(dataURL,name="wall-background.png"){
 const response=await fetch(dataURL);if(!response.ok)throw new Error("Could not restore the wall photo from this config.");
 const blob=await response.blob();return new File([blob],name,{type:blob.type||"image/png"});
}
function downloadJSON(filename,content){
 const blob=new Blob([content],{type:"application/json;charset=utf-8"});
 const url=URL.createObjectURL(blob),a=document.createElement("a");
 a.href=url;a.download=filename;a.style.display="none";document.body.appendChild(a);a.click();a.remove();
 window.setTimeout(()=>URL.revokeObjectURL(url),2000);
}
const exportConfigButton=$("exportConfig"),importConfigButton=$("importConfig"),configFileInput=$("configFile");
if(exportConfigButton) exportConfigButton.addEventListener("click",async()=>{
 try{
   exportConfigButton.disabled=true;
   const config={app:"ArtMockery",configVersion:1,settings:settings(),wallPhoto:null};
   if(wallFile)config.wallPhoto={name:wallFile.name||"wall-background.png",dataURL:await fileToDataURL(wallFile)};
   downloadJSON("artmockery-config.json",JSON.stringify(config,null,2));
   $("status").textContent=config.wallPhoto?"Config exported, including your custom wall photo.":"Config exported. Your wall settings are saved.";
 }catch(err){$("status").textContent="Config export failed: "+(err?.message||String(err));}
 finally{exportConfigButton.disabled=false;}
});
if(importConfigButton&&configFileInput){
 importConfigButton.addEventListener("click",()=>{
   // Reset the value first so importing the same file twice still triggers change.
   configFileInput.value="";
   configFileInput.click();
 });
 configFileInput.addEventListener("change",async e=>{
   const file=e.target.files&&e.target.files[0];if(!file)return;
   try{
     if(file.size>40*1024*1024)throw new Error("Config file is too large (maximum 40 MB).");
     const config=JSON.parse(await file.text());
     if(!config||!["ArtMockery","Art Mockup"].includes(config.app)||config.configVersion!==1||!config.settings||typeof config.settings!=="object")throw new Error("This is not a supported ArtMockery config file.");
     const s=config.settings;
     const validKeys=["wallColor","tint","texture","frame","orientation","frameColor","frameHighlightColor","frameShadowColor","matColor","frameWidth","matWidth","artZoom","artWidth","artHeight","artX","artY","shadow","outW","outH","format"];
     for(const key of validKeys){if(s[key]!==undefined&&$(key))$(key).value=s[key];}
     if(config.wallPhoto&&config.wallPhoto.dataURL){
       const restoredFile=await dataURLToFile(config.wallPhoto.dataURL,config.wallPhoto.name||"wall-background.png");
       const restoredImage=await loadImage(restoredFile);
       wallFile=restoredFile;wallImg=restoredImage;
       document.querySelectorAll(".preset").forEach(b=>b.classList.remove("active"));
       try{const dt=new DataTransfer();dt.items.add(restoredFile);$("wallphoto").files=dt.files;}catch(_){/* The in-memory wall photo still works if assigning FileList is restricted. */}
     }else{
       wallImg=null;wallFile=null;$("wallphoto").value="";
       const preset=s.preset||defaults.preset;
       document.querySelectorAll(".preset").forEach(b=>b.classList.toggle("active",b.dataset.preset===preset));
     }
     updateLabels();schedulePreview();
     $("status").textContent=config.wallPhoto?"Config loaded, including its wall photo. Upload a painting to reuse it.":"Config loaded. Upload a painting to reuse these settings.";
   }catch(err){$("status").textContent="Config import failed: "+(err?.message||String(err));}
   finally{e.target.value="";}
 });
}

$("painting").addEventListener("change",async e=>{const f=e.target.files[0];if(!f)return;try{paintingImg=await loadImage(f);paintingFile=f;$("status").textContent=`Loaded ${f.name}`;schedulePreview()}catch{$("status").textContent="Could not read that image."}});
$("wallphoto").addEventListener("change",async e=>{const f=e.target.files[0];if(!f)return;try{wallImg=await loadImage(f);wallFile=f;document.querySelectorAll(".preset").forEach(b=>b.classList.remove("active"));$("status").textContent=`Wall photo: ${f.name}`;schedulePreview()}catch{$("status").textContent="Could not read that wall photo."}});
$("reset").addEventListener("click",()=>{Object.entries(defaults).forEach(([k,v])=>{if($(k))$(k).value=v});wallImg=null;wallFile=null;$("wallphoto").value="";setPreset(defaults.preset);$("status").textContent="Settings reset.";updateLabels();$("previewZoom").value=100;$("previewZoomVal").textContent="100%";$("preview").style.setProperty("--preview-zoom",1);previewPanX=0;previewPanY=0;applyPreviewPan();schedulePreview()});
$("render").addEventListener("click",async()=>{
 if(!paintingFile){$("status").textContent="Please upload a painting first.";return}
 const btn=$("render");btn.disabled=true;$("status").textContent="Rendering full-resolution image…";
 try{
   const s=settings(),fd=new FormData();fd.append("painting",paintingFile);if(wallFile)fd.append("wall_photo",wallFile);
   fd.append("settings",JSON.stringify(s));
   const res=await fetch("/api/render",{method:"POST",body:fd});if(!res.ok)throw new Error(await res.text());
   const blob=await res.blob(),url=URL.createObjectURL(blob),a=document.createElement("a");
   a.href=url;a.download=`artmockery-${s.outW}x${s.outH}.${s.format==="JPEG"?"jpg":"png"}`;document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);
   $("status").textContent="Export ready — downloaded to your Downloads folder.";
 }catch(err){$("status").textContent="Render failed: "+err.message}
 finally{btn.disabled=false}
});
updateLabels();drawMockup($("preview"),settings());
