from pathlib import Path
import importlib.util,json,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('mannequin',ROOT.parent/'第二场人偶站位_20261104'/'render_scene2.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
W,H,SS=2048,1536,2
r.W,r.H,r.SS=W,H,SS
r.rgb=np.zeros((H*SS,W*SS,4),np.uint8)
r.depth=np.full((H*SS,W*SS),-1e9,np.float32)
right=np.array([.864,.504,0.]);up=np.array([-.413,.707,.574]);cam=np.cross(right,up)
S=185.;origin=np.array([420.,1075.])
active_rotation=np.eye(3)
def proj(p,anchor,scale):
    q=(np.asarray(p)@active_rotation.T)*scale+np.asarray(anchor)
    return np.stack((origin[0]+S*(q@right),origin[1]-S*(q@up),q@cam),axis=-1)
r.project=proj
A=(0,0,0)
def box(x,y,z,sx,sy,sz,col):
    vs=[(x+i*sx,y+j*sy,z+k*sz) for k in (0,1) for j in (0,1) for i in (0,1)]
    fs=[(0,1,3),(0,3,2),(4,6,7),(4,7,5),(0,4,5),(0,5,1),(2,3,7),(2,7,6),(0,2,6),(0,6,4),(1,5,7),(1,7,3)]
    r.mesh(vs,fs,col,A,1,0)
def rod(a,b,rad,col):r.segment(a,b,rad,rad,col,A,1,0)
def sphere(p,rad,col):r.ellipsoid(p,rad,col,A,1,0)
def table(x,y,sx,sy,h):
    for dx in (.07,sx-.12):
        for dy in (.07,sy-.12):box(x+dx,y+dy,.02,.07,.07,h-.05,(105,76,49))
    box(x,y,h-.08,sx,sy,.1,(143,109,70))
    for t in np.arange(.10,sy,.19):box(x+.01,y+t,h+.021,sx-.02,.008,.002,(110,84,57))
    for yy in (y+.01,y+sy-.07):box(x,yy,h-.22,sx,.06,.15,(113,81,51))
def stool(x,y,s=.43,h=.46):
    for xx in (x-s*.38,x+s*.28):
        for yy in (y-s*.38,y+s*.28):box(xx,yy,.01,.05,.05,h-.035,(111,78,48))
    box(x-s*.5,y-s*.5,h-.04,s,s,.06,(158,121,77))
def cylinder(x,y,z,rad,h,col):rod((x,y,z),(x,y,z+h),rad,col)
def stove(x,y,frying=False):
    cylinder(x,y,.03,.29,.69,(71,72,69))
    cylinder(x,y,.10,.301,.035,(112,108,94));cylinder(x,y,.65,.31,.035,(118,110,93))
    box(x-.14,y-.293,.22,.27,.025,.19,(37,35,30))
    sphere((x-.02,y-.315,.28),(.08,.022,.035),(210,91,38))
    sphere((x,y,.78),(.39,.36,.13),(59,59,53))
    sphere((x,y,.842),(.33,.30,.027),(87,78,56) if frying else (100,99,86))
    for side in (-1,1):rod((x+side*.30,y,.82),(x+side*.48,y,.85),.027,(50,47,39))
    if frying:
        for j in range(4):
            yy=y-.15+j*.09
            rod((x-.22,yy,.88),(x+.23,yy+.045,.88),.035,(204,151,67))
# Low cutaway walls keep the whole layout readable.
box(-.18,-.30,-.13,3.94,7.2,.13,(159,152,135))
rng=np.random.default_rng(23)
for row,y in enumerate(np.arange(-.24,6.85,.40)):
    for x in np.arange(-.10-(row%2)*.26,3.65,.53):
        xa=max(-.10,x);xb=min(3.65,x+.505)
        if xb<=xa:continue
        col=tuple(int(c+rng.uniform(-8,8)) for c in (183,180,163))
        box(xa,y,.001,xb-xa,.37,.018,col)
box(-.16,-.28,.01,.12,7.12,.25,(165,145,117))
box(3.65,-.28,.01,.10,7.12,.24,(164,145,121))
for y in np.arange(-.2,6.75,.42):
    box(-.175,y,.25,.15,.012,.025,(132,114,93))
# Kitchen layout, traced as an approximate spatial model from the supplied image.
stove(.35,.35,False)
# Covered aluminium porridge pot on the second original stove.
x,y=.42,1.36
cylinder(x,y,.03,.29,.69,(71,72,69))
cylinder(x,y,.10,.301,.035,(112,108,94));cylinder(x,y,.65,.31,.035,(118,110,93))
box(x-.14,y-.293,.22,.27,.025,.19,(37,35,30))
sphere((x-.02,y-.315,.28),(.08,.022,.035),(210,91,38))
cylinder(x,y,.70,.32,.22,(158,156,139))
sphere((x,y,.92),(.34,.33,.085),(186,183,165))
for xx in (x-.065,x+.065):rod((xx,y,.98),(xx,y,1.04),.022,(57,52,43))
rod((x-.065,y,1.04),(x+.065,y,1.04),.022,(57,52,43))
for side in (-1,1):rod((x+side*.29,y,.87),(x+side*.41,y,.87),.025,(86,81,68))
# Small work surface beside the stove, and the large wall-side bench.
table(.76,.96,.39,.61,.81)
table(.02,1.91,1.30,2.04,.88)
# Chopping board, condiments and the existing vegetable bowl.
cylinder(.73,2.63,.91,.20,.05,(146,106,61))
for j in range(3):
    cylinder(.20,2.13+j*.18,.91,.05,.22,(113+20*j,83+8*j,43))
    cylinder(.20,2.13+j*.18,1.13,.033,.025,(154,61,43))
sphere((.45,3.45,.99),(.25,.23,.12),(168,166,146))
for j in range(4):rod((.29+j*.07,3.35,1.08),(.37+j*.06,3.63,1.13),.025,(81,116,59))
# Nested cookware below the worktop.
for yy in (2.22,2.95,3.62):
    cylinder(.55,yy,.12,.22,.23,(127,129,117))
# Rear left sink: side walls and recessed basin, not a solid counter.
box(.02,4.08,.02,1.03,.86,.60,(155,151,127))
box(.02,4.08,.60,1.03,.86,.04,(111,116,104))
for xx in (.02,.98):box(xx,4.08,.62,.07,.86,.23,(169,164,138))
for yy in (4.08,4.87):box(.02,yy,.62,1.03,.07,.23,(169,164,138))
rod((.18,4.53,.84),(.18,4.53,1.14),.018,(146,147,132))
rod((.18,4.53,1.14),(.42,4.53,1.14),.018,(146,147,132))
rod((.42,4.53,1.14),(.42,4.53,1.05),.018,(146,147,132))
# Right-side shelf with its top work surface and existing stool.
for z in (.24,.77,1.30):box(3.15,4.40,z,.48,.65,.055,(121,104,79))
for xx in (3.15,3.57):
    for yy in (4.40,4.99):box(xx,yy,.10,.045,.045,1.32,(110,91,65))
sphere((3.38,4.72,1.40),(.18,.21,.09),(171,167,147))
sphere((3.37,4.72,.87),(.16,.18,.09),(180,175,156))
sphere((3.40,4.72,.81),(.20,.21,.065),(157,65,47))
sphere((3.35,4.72,.44),(.19,.20,.16),(93,76,55))
stool(2.90,4.96,.37,.46)
# Foreground right wash trough is separate from Wan's rear sink.
box(3.08,.06,.02,.56,.77,.55,(162,156,131))
box(3.12,.10,.53,.48,.69,.035,(113,112,95))
# Three people retain the colour coding of 第一场_人物站位.png.
source_config=ROOT.parent/'第一场_V8人偶站位_靠近案台修正版_20261103.json'
source=json.loads(source_config.read_text())
by_id={a['id']:a for a in source['people']}
people=[]
for pid,xyz,size in [('xiong',[1.20,1.30,0],.98),('woman',[1.66,2.02,0],.96),('wan',[1.50,4.56,0],1.0)]:
    a=dict(by_id[pid]);a.update(xyz=xyz,size=size)
    # The photo's projected arm elevations become worktop contact heights in 3-D.
    if pid=='woman':
        a['arms']=[[[-.13,.13,1.38],[-.30,.16,1.08],[-.40,.25,.94]],[[.12,-.13,1.38],[-.06,-.15,1.08],[-.36,.04,.94]]]
    people.append(a)
for a in people:r.puppet(a,a['xyz'],a['size'],0)
# Ladle is a pose marker; the supplied base image still has a covered pot.
hand=np.array(people[0]['xyz'])+np.array([-.62,.22,1.02])*.98
rod(hand,(.68,1.45,.95),.012,(135,134,118))
sphere((.68,1.45,.95),(.035,.045,.013),(149,149,133))
layer=Image.fromarray(r.rgb).resize((W,H),Image.Resampling.LANCZOS)
canvas=Image.new('RGBA',(W,H),(246,242,231,255))
# Soft contact shadow outside the ground slab.
shade=Image.new('RGBA',(W,H));sd=ImageDraw.Draw(shade)
poly=[tuple(proj(q,A,1)[:2]+[15,20]) for q in [(-.18,-.3,-.13),(3.76,-.3,-.13),(3.76,6.9,-.13),(-.18,6.9,-.13)]]
sd.polygon(poly,fill=(57,49,32,45));shade=shade.filter(ImageFilter.GaussianBlur(18))
canvas=Image.alpha_composite(canvas,shade);canvas=Image.alpha_composite(canvas,layer)
prefix=ROOT.parent.parent/'参考图'/'第一场_人物站位_偏俯视_20261104'
clean=canvas.convert('RGB');clean.save(str(prefix)+'_无字.png')
label=canvas.copy();d=ImageDraw.Draw(label)
font='/System/Library/Fonts/STHeiti Medium.ttc'
def f(n):return ImageFont.truetype(font,n)
d.text((80,55),'第一场 · 人物站位',font=f(44),fill='#292f2e')
d.text((82,119),'偏俯视站位示意  /  依据《第一场_人物站位.png》',font=f(23),fill='#6c7069')
def card(x,y,name,desc,col,target):
    width=max(d.textbbox((0,0),name,font=f(27))[2],d.textbbox((0,0),desc,font=f(20))[2])+42
    height=93
    edge=(x+width,y+height/2) if target[0]>x+width else (x,y+height/2)
    if x<target[0]<x+width:edge=(target[0],y+height if target[1]>y else y)
    d.line([tuple(target),edge],fill=col,width=3)
    d.ellipse((target[0]-4,target[1]-4,target[0]+4,target[1]+4),fill=col)
    d.rounded_rectangle((x,y,x+width,y+height),radius=12,fill='#fcfaf3',outline='#d7d2c5',width=2)
    d.rounded_rectangle((x,y,x+6,y+height),radius=3,fill=col)
    d.text((x+20,y+12),name,font=f(27),fill='#292e2d')
    d.text((x+20,y+54),desc,font=f(20),fill='#656c66')
def pt(x,y,z):return proj((x,y,z),A,1)[:2]
card(130,900,'熊庚香｜红色','粥锅通道侧，右手持勺','#b24b40',pt(1.20,1.30,1.55))
card(1430,940,'黑帽女人｜黄色','熊的右侧稍后，双手放稳油菜','#d3a740',pt(1.66,2.02,1.55))
card(1450,320,'万佐成｜蓝色','后方水槽通道侧，面向水槽清洗','#3e7daa',pt(1.50,4.56,1.55))
def note(text,xy,target):
    d.line([xy,tuple(target)],fill='#99988c',width=2)
    d.text((xy[0]+5,xy[1]-29),text,font=f(21),fill='#646b62',stroke_width=3,stroke_fill='#f6f2e7')
note('左后方水槽',(750,285),pt(.65,4.57,.85))
note('贴墙木案台',(390,530),pt(.55,3.0,.90))
note('粥锅（沿用原图盖锅状态）',(160,1125),pt(.42,1.36,.98))
note('近端炒锅',(510,1335),pt(.35,.35,.85))
note('右侧原有小桌 / 置物架',(1530,610),pt(3.38,4.72,1.35))
d.text((1600,190),'巷道深端 ↑',font=f(25),fill='#6c746c')
d.text((82,1440),'红：熊庚香   黄：黑帽女人   蓝：万佐成；三人均在工作区的通道侧。',font=f(23),fill='#555f57')
d.text((82,1480),'单图近似还原的空间示意；锅盖、近端炒锅沿用输入图状态。',font=f(21),fill='#7b8075')
label.convert('RGB').save(str(prefix)+'_标注.png')
(ROOT/'第一场_俯视站位配置.json').write_text(json.dumps({'source_image':'../../参考图/第一场_人物站位.png','camera':{'elevation_degrees':55,'projection':'orthographic'},'people':people,'notes':'人物位置与配色以用户指定图为准。按单张图近似还原布局，不代表真实空间测量。原锅盖、近端炒锅仍保留，未新增油桶菜袋；仅作为站位示意，不是完整分镜首帧。'},ensure_ascii=False,indent=2))
print(prefix)
