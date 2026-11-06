// 导航高亮
const links=[...document.querySelectorAll('.nav .menu a')];
const secs=links.map(a=>document.querySelector(a.getAttribute('href')));
const obs=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){const i=secs.indexOf(e.target);links.forEach(l=>l.classList.remove('on'));if(i>=0)links[i].classList.add('on');}})},{rootMargin:'-20% 0px -70% 0px'});
secs.forEach(s=>s&&obs.observe(s));

// ===== 图1：全片 5s 窗口 RMS（dB 原始值，0–193s） =====
const CURVE=[[0,-19.1],[5,-18.6],[10,-19.6],[15,-26.2],[20,-23.2],[25,-22.0],[30,-26.7],[35,-21.9],[40,-18.8],[45,-20.0],[50,-18.4],[55,-18.3],[60,-21.5],[65,-19.7],[70,-20.3],[75,-21.3],[80,-19.2],[85,-27.0],[90,-19.2],[95,-19.0],[100,-19.0],[105,-20.5],[110,-32.8],[115,-59.5],[118,-90.3],[120,-30.4],[125,-20.9],[130,-17.9],[135,-20.2],[140,-19.1],[145,-35.4],[150,-26.0],[155,-22.6],[160,-25.8],[165,-23.0],[170,-22.5],[175,-28.7],[180,-33.0],[185,-34.8],[190,-42.5]];
const AREAS=[
  {name:'一幕 广场·冷',s:0,e:36,tone:'cool'},
  {name:'二幕 家访·暖',s:36,e:88,tone:'warm'},
  {name:'三幕 便利店·冷',s:88,e:112,tone:'cool'},
  {name:'产品揭示·暖',s:112,e:125.2,tone:'warm'},
  {name:'归家·送枕·暖',s:125.2,e:149.5,tone:'warm'},
  {name:'卧室·谈心·暖',s:149.5,e:178.4,tone:'warm'},
  {name:'调查·落版·冷',s:178.4,e:193.2,tone:'cool'}
];
const FLASH=[19.9,35.9,88.1,112.4,125.2,141.6,149.5,163.6,166.8,178.4,181.6,187.9];
const warm='rgba(216,154,78,', cool='rgba(138,160,189,';
function tc(s){var m=Math.floor(s/60),x=Math.round(s%60);return m+':'+String(x).padStart(2,'0');}
const c1=echarts.init(document.getElementById('chartCurve'));
c1.setOption({
  grid:{left:52,right:24,top:38,bottom:44},
  tooltip:{trigger:'axis',backgroundColor:'#232732',borderColor:'rgba(231,227,216,.2)',textStyle:{color:'#e7e3d8',fontSize:12},
    formatter:function(p){var d=p[0].data;return tc(d[0])+' 附近 5s 窗口：'+d[1]+' dB';}},
  xAxis:{type:'value',min:0,max:193,interval:20,name:'秒',nameTextStyle:{color:'#8f8b81',fontSize:10},axisLine:{lineStyle:{color:'rgba(231,227,216,.2)'}},axisLabel:{color:'#8f8b81',fontSize:10.5,formatter:function(v){return tc(v);}}},
  yAxis:{type:'value',min:-95,max:-10,interval:10,name:'RMS(dB)',nameTextStyle:{color:'#8f8b81',fontSize:10},axisLabel:{color:'#8f8b81',fontSize:10.5},splitLine:{lineStyle:{color:'rgba(231,227,216,.08)'}}},
  series:[{
    type:'line',data:CURVE,smooth:true,symbol:'circle',symbolSize:4,
    itemStyle:{color:'#d89a4e'},
    lineStyle:{color:'#d89a4e',width:2.2},
    areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(216,154,78,.45)'},{offset:1,color:'rgba(216,154,78,.02)'}])},
    markArea:{silent:true,data:AREAS.map(a=>[{name:a.name,xAxis:a.s,itemStyle:{color:(a.tone==='warm'?warm:cool)+'.07)'}},{xAxis:a.e}]),
      label:{color:'#8f8b81',fontSize:10,position:'insideTop'}},
    markPoint:{symbol:'circle',symbolSize:8,data:FLASH.map(t=>({coord:[t,(function(){var near=CURVE.reduce(function(b,p){return Math.abs(p[0]-t)<Math.abs(b[0]-t)?p:b;});return near[1];})()],itemStyle:{color:'#e7e3d8'}})),label:{show:false}},
    markLine:{silent:true,symbol:'none',lineStyle:{color:'rgba(231,227,216,.35)',type:'dashed'},data:[{xAxis:120,label:{formatter:'分段边界 02:00',color:'#8f8b81',fontSize:10}}]}
  }]
});

// ===== 图2：七段镜头/切点节奏 =====
const SEG_NAMES=['一幕·广场','二幕·家访','三幕·再访','四幕①产品余韵','四幕②归家送枕','四幕③卧室谈心','四幕④调查落版'];
const SEG_SHOTS=[12,19,8,1,15,13,4];
const SEG_CUTS=[13,38,15,0,15,16,1];
const c2=echarts.init(document.getElementById('chartRhythm'));
c2.setOption({
  grid:{left:46,right:20,top:48,bottom:70},
  tooltip:{trigger:'axis',backgroundColor:'#232732',borderColor:'rgba(231,227,216,.2)',textStyle:{color:'#e7e3d8',fontSize:12}},
  legend:{data:['段落镜头数','硬切点数（0.12阈值）'],textStyle:{color:'#c9c4b8',fontSize:11.5},top:8},
  xAxis:{type:'category',data:SEG_NAMES,axisLine:{lineStyle:{color:'rgba(231,227,216,.2)'}},axisLabel:{color:'#8f8b81',fontSize:10,interval:0,rotate:18}},
  yAxis:{type:'value',axisLabel:{color:'#8f8b81',fontSize:10.5},splitLine:{lineStyle:{color:'rgba(231,227,216,.08)'}}},
  series:[
    {name:'段落镜头数',type:'bar',barWidth:18,data:SEG_SHOTS,itemStyle:{color:'#8aa0bd',borderRadius:[3,3,0,0]}},
    {name:'硬切点数（0.12阈值）',type:'bar',barWidth:18,data:SEG_CUTS,itemStyle:{color:'#d89a4e',borderRadius:[3,3,0,0]}}
  ]
});

// ===== 图3：1s 窗口归一化能量（两段分别归一化，仅看分段内节奏） =====
const F1S=[[0.0,0.905],[1.0,0.967],[2.0,0.924],[3.0,0.964],[4.0,0.945],[5.0,0.983],[6.0,0.929],[7.0,0.967],[8.0,0.917],[9.0,0.939],[10.0,0.949],[11.0,0.879],[12.0,0.998],[13.0,0.863],[14.0,0.866],[15.0,0.874],[16.0,0.909],[17.0,0.707],[18.0,0.649],[19.0,0.809],[20.0,0.681],[21.0,0.936],[22.0,0.907],[23.0,0.887],[24.0,0.87],[25.0,0.831],[26.0,0.909],[27.0,0.899],[28.0,0.905],[29.0,0.944],[30.0,0.795],[31.0,0.91],[32.0,0.755],[33.0,0.669],[34.0,0.797],[35.0,0.751],[36.0,0.84],[37.0,0.88],[38.0,0.959],[39.0,0.934],[40.0,0.971],[41.0,1.0],[42.0,0.912],[43.0,0.813],[44.0,0.96],[45.0,0.934],[46.0,0.938],[47.0,0.968],[48.0,0.788],[49.0,0.954],[50.0,0.941],[51.0,0.907],[52.0,0.926],[53.0,0.982],[54.0,0.945],[55.0,0.979],[56.0,0.924],[57.0,0.933],[58.0,0.984],[59.0,0.911],[60.0,0.845],[61.0,0.96],[62.0,0.882],[63.0,0.934],[64.0,0.941],[65.0,0.912],[66.0,0.958],[67.0,0.77],[68.0,0.95],[69.0,0.943],[70.0,0.951],[71.0,0.941],[72.0,0.942],[73.0,0.864],[74.0,0.931],[75.0,0.812],[76.0,0.839],[77.0,0.947],[78.0,0.889],[79.0,0.96],[80.0,0.951],[81.0,0.988],[82.0,0.788],[83.0,0.92],[84.0,0.927],[85.0,0.88],[86.0,0.706],[87.0,0.754],[88.0,0.68],[89.0,0.699],[90.0,0.969],[91.0,0.961],[92.0,0.935],[93.0,0.953],[94.0,0.958],[95.0,0.958],[96.0,0.914],[97.0,0.923],[98.0,0.964],[99.0,0.962],[100.0,0.93],[101.0,0.863],[102.0,0.976],[103.0,0.946],[104.0,0.892],[105.0,0.964],[106.0,0.973],[107.0,0.794],[108.0,0.844],[109.0,0.771],[110.0,0.827],[111.0,0.689],[112.0,0.669],[113.0,0.583],[114.0,0.448],[115.0,0.373],[116.0,0.267],[117.0,0.027],[118.0,0.023],[119.0,0.0],[120.0,0.608],[121.0,0.654],[122.0,0.602],[123.0,0.158],[124.0,0.183],[125.0,0.545],[126.0,0.349],[127.0,0.85],[128.0,0.916],[129.0,0.864],[130.0,1.0],[131.0,0.866],[132.0,0.886],[133.0,0.921],[134.0,0.33],[135.0,0.847],[136.0,0.929],[137.0,0.858],[138.0,0.768],[139.0,0.597],[140.0,0.542],[141.0,0.921],[142.0,0.837],[143.0,0.94],[144.0,0.864],[145.0,0.42],[146.0,0.46],[147.0,0.42],[148.0,0.46],[149.0,0.332],[150.0,0.289],[151.0,0.433],[152.0,0.662],[153.0,0.839],[154.0,0.556],[155.0,0.681],[156.0,0.308],[157.0,0.793],[158.0,0.828],[159.0,0.85],[160.0,0.441],[161.0,0.711],[162.0,0.433],[163.0,0.422],[164.0,0.834],[165.0,0.627],[166.0,0.807],[167.0,0.779],[168.0,0.755],[169.0,0.787],[170.0,0.76],[171.0,0.744],[172.0,0.673],[173.0,0.823],[174.0,0.828],[175.0,0.757],[176.0,0.578],[177.0,0.289],[178.0,0.422],[179.0,0.523],[180.0,0.515],[181.0,0.501],[182.0,0.499],[183.0,0.444],[184.0,0.49],[185.0,0.499],[186.0,0.474],[187.0,0.409],[188.0,0.425],[189.0,0.36],[190.0,0.286],[191.0,0.264],[192.0,0.125],[193.0,0.0]];
const c3=echarts.init(document.getElementById('chart1s'));
c3.setOption({
  grid:{left:46,right:24,top:30,bottom:44},
  tooltip:{trigger:'axis',backgroundColor:'#232732',borderColor:'rgba(231,227,216,.2)',textStyle:{color:'#e7e3d8',fontSize:12},
    formatter:function(p){var d=p[0].data;return tc(d[0])+'：'+d[1].toFixed(2);}},
  xAxis:{type:'value',min:0,max:193,interval:20,axisLine:{lineStyle:{color:'rgba(231,227,216,.2)'}},axisLabel:{color:'#8f8b81',fontSize:10.5,formatter:function(v){return tc(v);}}},
  yAxis:{type:'value',min:0,max:1.1,axisLabel:{color:'#8f8b81',fontSize:10.5},splitLine:{lineStyle:{color:'rgba(231,227,216,.08)'}}},
  series:[{
    type:'line',data:F1S,smooth:true,symbol:'none',
    lineStyle:{color:'#8aa0bd',width:1.6},
    areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(138,160,189,.35)'},{offset:1,color:'rgba(138,160,189,.02)'}])},
    markLine:{silent:true,symbol:'none',lineStyle:{color:'rgba(216,154,78,.6)',type:'dashed'},data:[{xAxis:120,label:{formatter:'02:00 分段（归一化口径不同）',color:'#d89a4e',fontSize:10}}]}
  }]
});
window.addEventListener('resize',()=>{c1.resize();c2.resize();c3.resize();});
