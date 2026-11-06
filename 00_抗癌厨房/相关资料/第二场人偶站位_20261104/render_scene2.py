#!/usr/bin/env python3
"""Composite articulated mannequins onto an unchanged scene from a JSON config.
Dependencies: Pillow, numpy. Coordinates and CLI are documented in references/render-config.md.
"""
from pathlib import Path
import argparse
import json
import math
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor

light = np.array([-.55,-.75,1.0]); light /= np.linalg.norm(light)
wood = (223,200,157)
joint = (116,98,75)

def project(p, anchor, scale):
    p = np.asarray(p)
    return np.stack((anchor[0]+scale*p[...,0],anchor[1]-scale*(p[...,2]+.22*p[...,1]),-p[...,1]+.22*p[...,2]),axis=-1)

def triangle(p, col):
    p=p.copy(); p[:,:2]*=SS
    lo=np.maximum(np.floor(p[:,:2].min(0)).astype(int),[0,0]); hi=np.minimum(np.ceil(p[:,:2].max(0)).astype(int),[W*SS-1,H*SS-1])
    if np.any(lo>hi): return
    xs,ys=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
    x0,y0=p[0,:2]; x1,y1=p[1,:2]; x2,y2=p[2,:2]
    den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
    if abs(den)<1e-7:return
    a=((y1-y2)*(xs-x2)+(x2-x1)*(ys-y2))/den
    b=((y2-y0)*(xs-x2)+(x0-x2)*(ys-y2))/den
    c=1-a-b
    z=a*p[0,2]+b*p[1,2]+c*p[2,2]
    target=depth[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
    mask=(a>=-1e-5)&(b>=-1e-5)&(c>=-1e-5)&(z>target)
    target[mask]=z[mask]
    targetrgb=rgb[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
    targetrgb[mask]=(*col,255)

def mesh(v, faces, col, anchor, scale, layer):
    v=np.array(v,float); screen=project(v,anchor,scale);screen[:,2]+=layer
    for ids in faces:
        tri=v[list(ids)]; n=np.cross(tri[1]-tri[0],tri[2]-tri[0]); nl=np.linalg.norm(n)
        if nl<1e-9:continue
        n/=nl
        center=tri.mean(0)
        # Double sided illumination keeps jointed forms legible.
        strength=.66+.30*abs(np.dot(n,light))+.04*n[2]
        color=tuple(int(np.clip(k*strength,0,255)) for k in col)
        triangle(screen[list(ids)],color)

def ellipsoid(center, radii, col, anchor, scale, layer, rot=None):
    v=[]; faces=[]; rows=18; cols=30
    for i in range(rows+1):
        t=math.pi*i/rows
        for j in range(cols):
            p=math.tau*j/cols
            q=np.array([radii[0]*math.sin(t)*math.cos(p),radii[1]*math.sin(t)*math.sin(p),radii[2]*math.cos(t)])
            if rot is not None:q=rot@q
            v.append(np.asarray(center)+q)
    for i in range(rows):
        for j in range(cols):
            a=i*cols+j;b=i*cols+(j+1)%cols;c=(i+1)*cols+j;d=(i+1)*cols+(j+1)%cols
            faces.extend([(a,c,b),(b,c,d)])
    mesh(v,faces,col,anchor,scale,layer)

def segment(a,b,r1,r2,col,anchor,scale,layer):
    a=np.array(a,float);b=np.array(b,float);axis=b-a;axis/=np.linalg.norm(axis)
    other=np.array([0.,1.,0.]) if abs(axis[1])<.9 else np.array([1.,0.,0.])
    u=np.cross(axis,other);u/=np.linalg.norm(u);v=np.cross(axis,u)
    vertices=[];faces=[];N=24
    for p,r in [(a,r1),(b,r2)]:
        for i in range(N):vertices.append(p+r*(u*math.cos(math.tau*i/N)+v*math.sin(math.tau*i/N)))
    vertices.extend([a,b])
    for i in range(N):
        j=(i+1)%N
        faces.extend([(i,j,i+N),(j,j+N,i+N),(2*N,j,i),(2*N+1,i+N,j+N)])
    mesh(vertices,faces,col,anchor,scale,layer)

def puppet(person, anchor, scale, layer):
    col=ImageColor.getrgb(person.get('color','#b24b40'))
    pose=person.get('pose','stand')
    mirror=1 if person.get('facing','left')=='left' else -1
    def vec(v):
        q=np.array(v,float);q[0]*=mirror;return q
    seated=person.get('seated',False)
    drop=.43 if seated else 0
    hip=vec([0,0,.94-drop]);chest=vec([-.025,.025,1.30-drop]);neck=vec([-.045,.025,1.49-drop])
    legs=[([-.10,.06,.92],[-.12,.07,.51],[-.14,.08,.08]),([.11,-.06,.92],[.14,-.06,.51],[.16,-.06,.08])]
    presets={
      'stand':[([-.13,.13,1.38],[-.17,.14,1.09],[-.18,.14,.83]),([.12,-.13,1.38],[.19,-.13,1.09],[.20,-.13,.83])],
      'talk':[([-.13,.13,1.38],[-.27,.12,1.15],[-.43,.09,1.22]),([.12,-.13,1.38],[.19,-.13,1.09],[.20,-.13,.83])],
      'stir':[([-.13,.13,1.38],[-.40,.18,1.15],[-.62,.22,1.02]),([.12,-.13,1.38],[-.09,-.22,1.17],[-.44,-.13,1.14])],
      'place':[([-.13,.13,1.38],[-.32,.22,1.18],[-.57,.28,1.03]),([.12,-.13,1.38],[-.09,-.13,1.14],[-.50,.01,1.02])],
      'wash':[([-.18,.18,1.36],[-.39,.23,1.12],[-.64,.29,.93]),([.06,-.10,1.36],[-.24,-.12,1.05],[-.59,.06,.91])]
    }
    if pose=='wash':
        chest=vec([-.09,.05,1.29]);neck=vec([-.14,.07,1.47])
    arms=person.get('arms',presets[pose]);legs=person.get('legs',legs)
    if seated:
        arms=[[[x,y,z-drop] for x,y,z in limb] for limb in arms]
        legs=person.get('legs',[[[-.10,.06,.49],[-.37,-.11,.46],[-.38,-.12,.08]],[[.11,-.06,.49],[-.17,-.28,.46],[-.18,-.29,.08]]])
    for h,k,a in legs:
        h,k,a=map(vec,(h,k,a))
        ellipsoid(h,(.08,.08,.08),joint,anchor,scale,layer)
        segment(h,k,.095,.073,col,anchor,scale,layer)
        ellipsoid(k,(.075,.075,.075),wood,anchor,scale,layer)
        segment(k,a,.066,.046,col,anchor,scale,layer)
        ellipsoid(a,(.048,.048,.048),wood,anchor,scale,layer)
        ellipsoid(a+vec([-.045,-.025,-.035]),(.115,.07,.045),(68,61,53),anchor,scale,layer)
    ellipsoid(hip,(.17,.125,.125),col,anchor,scale,layer)
    ellipsoid(hip+vec([0,0,.16]),(.09,.09,.095),wood,anchor,scale,layer)
    segment(hip+vec([0,0,.16]),chest,.105,.165,col,anchor,scale,layer)
    ellipsoid(chest,(.17,.115,.17),col,anchor,scale,layer)
    segment(chest,neck,.065,.055,wood,anchor,scale,layer)
    head=neck+vec([0,0,.15])
    ellipsoid(head,(.108,.095,.139),wood,anchor,scale,layer)
    yaw=math.radians(person.get('head_yaw_degrees',-150))
    forward=vec([math.cos(yaw),math.sin(yaw),0])
    ellipsoid(head+forward*.099+vec([0,0,.005]),(.033,.033,.027),wood,anchor,scale,layer)
    hands=[]
    for sh,el,ha in arms:
        sh,el,ha=map(vec,(sh,el,ha))
        ellipsoid(sh,(.077,.077,.077),wood,anchor,scale,layer)
        segment(sh,el,.067,.053,col,anchor,scale,layer)
        ellipsoid(el,(.054,.054,.054),wood,anchor,scale,layer)
        segment(el,ha,.046,.030,wood,anchor,scale,layer)
        ellipsoid(ha,(.045,.037,.06),wood,anchor,scale,layer)
        hands.append(project(ha,anchor,scale))
    if person.get('hat',False):
        ellipsoid(head+vec([0,0,.093]),(.113,.102,.065),(37,35,33),anchor,scale,layer)
        ellipsoid(head+vec([0,0,.061]),(.147,.132,.015),(27,26,24),anchor,scale,layer)
    if person.get('bag',False):
        hand=arms[1][2]
        hx,hy,hz=hand
        bagcol=(91,132,70)
        segment(vec([hx,hy,hz-.03]),vec([hx,hy,hz-.18]),.012,.012,(118,112,88),anchor,scale,layer)
        ellipsoid(vec([hx,hy,hz-.32]),(.13,.085,.17),bagcol,anchor,scale,layer)
        for dx in (-.07,0,.06):
            ellipsoid(vec([hx+dx,hy,hz-.17]),(.035,.04,.08),(75,108,58),anchor,scale,layer)
    return hands


def resolve(config_path,value):
    p=Path(value).expanduser()
    return p if p.is_absolute() else config_path.parent/p


def validate(config):
    people=config['people']
    if not isinstance(people,list) or not people:raise ValueError('people must be a non-empty list')
    ids=set()
    for p in people:
        if not p.get('id') or p['id'] in ids:raise ValueError('Every person needs a unique id')
        ids.add(p['id'])
        if len(p['foot'])!=2 or not all(0<=float(v)<=1 for v in p['foot']):raise ValueError('foot must be normalized [u,v] in [0,1]')
        if not 0<float(p['height_ratio'])<=2:raise ValueError('height_ratio must be in (0,2]')
        if p.get('pose','stand') not in ('stand','talk','stir','place','wash'):raise ValueError('Unknown pose')
        if p.get('facing','left') not in ('left','right'):raise ValueError('facing must be left or right')
        ImageColor.getrgb(p.get('color','#b24b40'))
        for key in ('arms','legs'):
            if key in p:
                arr=np.asarray(p[key],dtype=float)
                if arr.shape!=(2,3,3) or not np.isfinite(arr).all():raise ValueError(key+' must have shape [2,3,3] and finite coordinates')
                if np.any(np.linalg.norm(np.diff(arr,axis=1),axis=2)<1e-6):raise ValueError(key+' has a zero-length limb segment')
    for tool in config.get('tools',[]):
        if tool['person'] not in ids or tool.get('hand',0) not in (0,1):raise ValueError('Invalid tool person/hand')
        if len(tool['target'])!=2 or not all(0<=float(v)<=1 for v in tool['target']):raise ValueError('Invalid tool target')


def find_font(config,config_path):
    choices=[str(resolve(config_path,config['font']))] if config.get('font') else []
    choices += ['/System/Library/Fonts/STHeiti Medium.ttc','/System/Library/Fonts/PingFang.ttc','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc','C:/Windows/Fonts/msyh.ttc']
    for p in choices:
        if Path(p).is_file():return p
    raise ValueError('No CJK font found; set font in config or run --clean-only')


def main():
    global SS,W,H,rgb,depth
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True,type=Path)
    parser.add_argument('--output-prefix',type=Path,help='Override config prefix; relative to current directory')
    parser.add_argument('--clean-only',action='store_true')
    parser.add_argument('--overwrite',action='store_true')
    args=parser.parse_args()
    config_path=args.config.expanduser().resolve()
    config=json.loads(config_path.read_text(encoding='utf-8'));validate(config)
    prefix=(args.output_prefix.expanduser().resolve() if args.output_prefix else resolve(config_path,config['output_prefix']).resolve())
    clean_path=Path(str(prefix)+'_无字.png');label_path=Path(str(prefix)+'_标注.png')
    targets=[clean_path] if args.clean_only else [clean_path,label_path]
    for p in targets:
        if p.exists() and not args.overwrite:raise ValueError(str(p)+' already exists; choose a new prefix or explicitly use --overwrite')
    font_path=None if args.clean_only else find_font(config,config_path)
    original=Image.open(resolve(config_path,config['scene'])).convert('RGBA')
    W,H=original.size;SS=int(config.get('supersample',2))
    if SS not in (1,2,3):raise ValueError('supersample must be 1, 2 or 3')
    base=Image.new('RGBA',(W*SS,H*SS))
    rgb=np.zeros((H*SS,W*SS,4),np.uint8);depth=np.full((H*SS,W*SS),-1e9,dtype=np.float32)
    shadow=Image.new('RGBA',base.size);sd=ImageDraw.Draw(shadow)
    people=sorted(config['people'],key=lambda p:p['foot'][1])
    for p in people:
        x,y=p['foot'][0]*W,p['foot'][1]*H;h=p['height_ratio']*H
        rx=h*.12;ry=h*.024
        sd.ellipse(tuple(round(v*SS) for v in (x-rx,y-ry,x+rx,y+ry)),fill=(24,20,13,80))
    base=Image.alpha_composite(base,shadow.filter(ImageFilter.GaussianBlur(max(1,W/410*SS))))
    all_hands={}
    for i,p in enumerate(people):
        anchor=(p['foot'][0]*W,p['foot'][1]*H);scale=p['height_ratio']*H/1.8
        if p.get('occlusion_mask'):
            previous_rgb=rgb.copy();previous_depth=depth.copy()
        all_hands[p['id']]=puppet(p,anchor,scale,i*5)
        if p.get('occlusion_mask'):
            pm=Image.open(resolve(config_path,p['occlusion_mask'])).convert('L').resize((W*SS,H*SS),Image.Resampling.NEAREST)
            keep=np.asarray(pm)>127
            rgb[keep]=previous_rgb[keep];depth[keep]=previous_depth[keep]

    result=Image.alpha_composite(base,Image.fromarray(rgb))
    d=ImageDraw.Draw(result)
    for t in config.get('tools',[]):
        hand=all_hands[t['person']][t.get('hand',0)];target=(t['target'][0]*W,t['target'][1]*H)
        points=[(round(hand[0]*SS),round(hand[1]*SS)),(round(target[0]*SS),round(target[1]*SS))]
        d.line(points,fill=t.get('color','#76736a'),width=max(1,round(t.get('width_px',4)*SS)))
        if t.get('bowl',False):
            x,y=target;rx=W*.006;ry=W*.003
            d.ellipse(tuple(round(v*SS) for v in (x-rx,y-ry,x+rx,y+ry)),fill=(128,126,117,255))
    result=Image.alpha_composite(original,result.resize((W,H),Image.Resampling.LANCZOS))
    if config.get('foreground_mask'):
        mask=Image.open(resolve(config_path,config['foreground_mask'])).convert('L')
        if mask.size!=(W,H):raise ValueError('foreground_mask size must match the scene')
        result=Image.composite(original,result,mask)
    clean=result.convert('RGB')
    labelled=None
    if not args.clean_only:
        labelled=result.copy();ld=ImageDraw.Draw(labelled)
        fs=max(14,round(W*.01172));ss=max(11,round(fs*.79));pad=max(8,round(fs*.625))
        font=ImageFont.truetype(font_path,fs);small=ImageFont.truetype(font_path,ss)
        for p in people:
            title=p.get('name',p['id']);subtitle=p.get('label','')
            width=max(ld.textbbox((0,0),title,font=font)[2],ld.textbbox((0,0),subtitle,font=small)[2])+pad*2
            height=round(fs*2.92) if subtitle else fs+pad*2
            if 'label_xy' in p:x,y=p['label_xy'][0]*W,p['label_xy'][1]*H
            else:x,y=p['foot'][0]*W+p['height_ratio']*H*.18,p['foot'][1]*H-p['height_ratio']*H*.92
            x=max(0,min(round(x),W-width));y=max(0,min(round(y),H-height))
            ld.rounded_rectangle((x,y,x+width,y+height),radius=round(fs*.4),fill=(20,25,28,235))
            ld.rounded_rectangle((x,y,x+max(3,round(fs*.21)),y+height),radius=2,fill=p.get('color','#b24b40'))
            ld.text((x+pad,y+round(fs*.375)),title,font=font,fill='white')
            if subtitle:ld.text((x+pad,y+round(fs*1.67)),subtitle,font=small,fill=(225,225,218,255))
    prefix.parent.mkdir(parents=True,exist_ok=True)
    clean.save(clean_path)
    if labelled is not None:labelled.convert('RGB').save(label_path)
    print(json.dumps({'size':[W,H],'people':len(people),'outputs':[str(p) for p in targets]},ensure_ascii=False))

if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError) as exc:
        print('Error: '+str(exc),file=sys.stderr);sys.exit(2)
