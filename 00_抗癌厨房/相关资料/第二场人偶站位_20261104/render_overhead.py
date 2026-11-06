from pathlib import Path
import importlib.util,json,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('mannequin',ROOT/'render_scene2.py')
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
# Original left-hand work zone: fry pan, spare-fire stove, wall-side bench.
stove(.35,.35,True);stove(.42,1.36,False)
table(.02,2.02,.98,2.03,.88)
# Small bowl and breakfast basket are identifiers, not new story props.
sphere((.40,2.70,.99),(.27,.25,.12),(169,169,151))
sphere((.50,3.40,.95),(.27,.20,.065),(158,117,62))
for j in range(4):rod((.32,3.30+j*.06,1.005),(.69,3.30+j*.06,1.005),.025,(218,165,79))
# Existing front stool remains pending the later move.
stool(1.01,.56,.48,.46)
# Rear dining table and all three separate seats.
table(.60,4.83,1.10,.78,.74)
stool(1.10,5.92,.40,.46)
stool(2.05,5.22,.40,.46)
stool(1.10,4.39,.40,.46)
# Right-side landmarks from the reference.
for z in (.24,.77,1.30):box(3.15,4.40,z,.48,.65,.055,(121,104,79))
for x in (3.15,3.57):
    for y in (4.40,4.99):box(x,y,.10,.045,.045,1.57,(110,91,65))
sphere((3.38,4.72,1.40),(.18,.21,.09),(171,167,147))
sphere((3.37,4.72,.87),(.16,.18,.09),(187,171,146))
sphere((3.40,4.72,.34),(.18,.20,.08),(157,65,47))
sphere((3.35,3.70,.39),(.27,.26,.38),(93,76,55))
cylinder(3.30,3.02,.025,.16,.32,(147,146,127))
box(3.08,.06,.02,.56,.77,.55,(162,156,131))
box(3.12,.10,.53,.48,.69,.035,(113,112,95))
# Full articulated seated and standing puppets, rendered with one shared 3-D camera.
people=[
 {'id':'boy','name':'男孩','color':'#54b9ac','xyz':[1.10,5.93,.15],'size':.67,'seated':True,'pose':'place','facing':'left','head_yaw_degrees':180,'body_yaw_degrees':90},
 {'id':'father','name':'父亲','color':'#537fc0','xyz':[2.05,5.23,0],'size':.97,'seated':True,'pose':'place','facing':'left','head_yaw_degrees':-150},
 {'id':'xiong','name':'熊庚香','color':'#d5a33b','xyz':[1.42,3.44,0],'size':.96,'pose':'place','facing':'left','head_yaw_degrees':-150},
 {'id':'wan','name':'万佐成','color':'#b85f49','xyz':[1.42,1.37,0],'size':1.02,'pose':'stand','facing':'right','head_yaw_degrees':-160},
 {'id':'mother','name':'母亲','color':'#a076ba','xyz':[2.48,1.69,0],'size':.96,'pose':'talk','facing':'left','head_yaw_degrees':-170,'bag':True},
]
for p in people:
    angle=math.radians(p.get('body_yaw_degrees',0))
    active_rotation=np.array([[math.cos(angle),-math.sin(angle),0],[math.sin(angle),math.cos(angle),0],[0,0,1]])
    r.puppet(p,p['xyz'],p['size'],0)
active_rotation=np.eye(3)
layer=Image.fromarray(r.rgb).resize((W,H),Image.Resampling.LANCZOS)
canvas=Image.new('RGBA',(W,H),(246,242,231,255))
# Soft contact shadow outside the ground slab.
shade=Image.new('RGBA',(W,H));sd=ImageDraw.Draw(shade)
poly=[tuple(proj(q,A,1)[:2]+[15,20]) for q in [(-.18,-.3,-.13),(3.76,-.3,-.13),(3.76,6.9,-.13),(-.18,6.9,-.13)]]
sd.polygon(poly,fill=(57,49,32,45));shade=shade.filter(ImageFilter.GaussianBlur(18))
canvas=Image.alpha_composite(canvas,shade);canvas=Image.alpha_composite(canvas,layer)
prefix=ROOT.parent.parent/'参考图'/'第二场_V8人偶基准图_偏俯视_20261104'
clean=canvas.convert('RGB');clean.save(str(prefix)+'_无字.png')
label=canvas.copy();d=ImageDraw.Draw(label)
font='/System/Library/Fonts/STHeiti Medium.ttc'
def f(n):return ImageFont.truetype(font,n)
d.text((80,55),'第二场 · 开场借火',font=f(44),fill='#292f2e')
d.text((82,119),'偏俯视站位示意  /  按基准图布局作近似还原',font=f(23),fill='#6c7069')
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
card(720,150,'男孩｜青绿','坐在小桌远侧','#429e92',pt(1.10,5.93,1.03))
card(1540,350,'父亲｜蓝色','坐在孩子旁边','#537fc0',pt(2.05,5.23,1.25))
card(1210,700,'熊庚香｜金黄','案台通道侧，稍后方待手','#b8902f',pt(1.42,3.44,1.55))
card(115,875,'万佐成｜赭红','炉位通道侧，面向母亲','#b85f49',pt(1.42,1.37,1.55))
card(1450,1010,'母亲｜紫色','万的右侧，提菜开口借火','#a076ba',pt(2.48,1.69,1.55))
# Environment labels with fine neutral leaders.
def note(text,xy,target):
    d.line([xy,tuple(target)],fill='#99988c',width=2)
    d.text((xy[0]+5,xy[1]-29),text,font=f(21),fill='#646b62',stroke_width=3,stroke_fill='#f6f2e7')
note('原有后方小桌',(1450,520),pt(1.55,5.0,.75))
note('留给母亲的小凳',(1200,650),pt(1.10,4.39,.49))
note('木案台',(420,560),pt(.4,3.0,.90))
note('待借炉位',(190,1080),pt(.42,1.36,.8))
note('待挪空凳',(645,1350),pt(1.01,.56,.49))
d.text((1600,190),'巷道深端 ↑',font=f(25),fill='#6c746c')
d.text((82,1440),'机位抬高以减少遮挡；五人的前后关系沿用开场站位。',font=f(23),fill='#555f57')
d.text((82,1480),'空间调度示意，非照片换机位实拍；人物服装、外貌以角色参考图为准。',font=f(21),fill='#7b8075')
label.convert('RGB').save(str(prefix)+'_标注.png')
(ROOT/'偏俯视站位.json').write_text(json.dumps({'camera':{'elevation_degrees':55,'projection':'orthographic'},'people':people,'notes':'根据原图作近似三维布局；不作为真实测量。原炉空锅和前景待挪空凳仍在原位。'},ensure_ascii=False,indent=2))
print(prefix)
