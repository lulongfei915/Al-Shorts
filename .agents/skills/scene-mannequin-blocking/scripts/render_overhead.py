#!/usr/bin/env python3
"""Render an approximate overhead blocking model from portable JSON (Pillow, numpy)."""
from pathlib import Path
import argparse
import importlib.util
import json
import math
import sys

import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageFont

SPEC = importlib.util.spec_from_file_location('blocking_core', Path(__file__).with_name('render_mannequins.py'))
core = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(core)


def vector(value, n, name, positive=False):
    a = np.asarray(value, dtype=float)
    if a.shape != (n,) or not np.isfinite(a).all() or (positive and np.any(a <= 0)):
        raise ValueError(f'{name} must contain {n} finite' + (' positive' if positive else '') + ' numbers')
    return a


def validate(config):
    size = vector(config.get('canvas', [2048, 1536]), 2, 'canvas', True)
    if np.any(size != np.floor(size)) or np.any(size < 256) or np.any(size > 8192):
        raise ValueError('canvas dimensions must be integers in [256, 8192]')
    ss = config.get('supersample', 2)
    if ss not in (1, 2, 3):
        raise ValueError('supersample must be 1, 2 or 3')
    camera = config.get('camera', {})
    el = float(camera.get('elevation_degrees', 55))
    az = float(camera.get('azimuth_degrees', -60))
    if not math.isfinite(el) or not 10 <= el <= 90 or not math.isfinite(az):
        raise ValueError('camera elevation must be in [10, 90]; azimuth must be finite')
    bounds = vector(config['floor']['bounds'], 4, 'floor.bounds')
    if bounds[2] <= bounds[0] or bounds[3] <= bounds[1]:
        raise ValueError('floor.bounds must be [xmin, ymin, xmax, ymax] with positive area')
    if config['floor'].get('tile_size') is not None:
        vector(config['floor']['tile_size'], 2, 'floor.tile_size', True)
    margins = vector(config.get('margins', [220, 210, 260, 180]), 4, 'margins')
    if np.any(margins < 0) or margins[0]+margins[2] >= size[0] or margins[1]+margins[3] >= size[1]:
        raise ValueError('margins [left, top, right, bottom] must leave a drawable area')
    if not config.get('output_prefix'):
        raise ValueError('output_prefix is required')
    people = config['people']
    if not isinstance(people, list) or not people:
        raise ValueError('people must be a non-empty list')
    # Reuse the photo renderer's identity, pose, colour and joint checks.
    core.validate({'people': [dict(p, foot=[.5, .5], height_ratio=.5) for p in people]})
    for p in people:
        vector(p['position'], 3, 'person.position')
        if not 0 < float(p.get('scale', 1)) <= 3:
            raise ValueError('person.scale must be in (0, 3]')
        for key in ('yaw_degrees', 'head_yaw_degrees'):
            if not math.isfinite(float(p.get(key, 0))):
                raise ValueError(key+' must be finite')
        if 'label_xy' in p:
            a = vector(p['label_xy'], 2, 'label_xy')
            if np.any(a < 0) or np.any(a > 1):
                raise ValueError('label_xy must be normalized to [0, 1]')
    types = {'box', 'table', 'stool', 'sink', 'shelf', 'stove', 'cylinder', 'ellipsoid', 'segment'}
    for obj in config.get('objects', []):
        kind = obj['type']
        if kind not in types:
            raise ValueError('Unknown object type: '+kind)
        if not math.isfinite(float(obj.get('yaw_degrees', 0))):
            raise ValueError('object.yaw_degrees must be finite')
        if 'color' in obj:
            ImageColor.getrgb(obj['color'])
        if kind == 'segment':
            start = vector(obj['start'], 3, 'segment.start')
            end = vector(obj['end'], 3, 'segment.end')
            if np.linalg.norm(start-end) < 1e-6 or not math.isfinite(float(obj['radius'])) or float(obj['radius']) <= 0:
                raise ValueError('segment needs distinct ends and a positive radius')
        else:
            vector(obj['position'], 3, 'object.position')
            if kind in ('box', 'table', 'stool', 'sink', 'shelf'):
                dims = vector(obj['size'], 3, 'object.size', True)
                if kind != 'box' and np.min(dims) < .15:
                    raise ValueError(kind+' dimensions must be >= 0.15 model units')
            elif kind == 'ellipsoid':
                vector(obj['radii'], 3, 'ellipsoid.radii', True)
            elif kind == 'cylinder':
                vector([obj['radius'], obj['height']], 2, 'cylinder radius/height', True)
            elif obj.get('vessel', 'pan') not in ('pan', 'covered_pot', 'empty'):
                raise ValueError('stove.vessel must be pan, covered_pot or empty')
    ids = {p['id'] for p in people}
    for tool in config.get('tools', []):
        if tool['person'] not in ids or tool.get('hand', 0) not in (0, 1):
            raise ValueError('tool needs a valid person and hand')
        vector(tool['target'], 3, 'tool.target')
        if not math.isfinite(float(tool.get('radius', .012))) or float(tool.get('radius', .012)) <= 0:
            raise ValueError('tool.radius must be positive')
    for note in config.get('notes', []):
        vector(note['target'], 3, 'note.target')
        a = vector(note['label_xy'], 2, 'note.label_xy')
        if np.any(a < 0) or np.any(a > 1):
            raise ValueError('note.label_xy must be normalized to [0, 1]')


class Model:
    """Record all geometry in one world space before fitting the camera."""
    def __init__(self):
        self.geometry = []
        self.rotation = np.eye(3)
        self.anchor = np.zeros(3)

    def world(self, points, anchor, scale):
        return (np.asarray(points, dtype=float)*scale) @ self.rotation.T + anchor

    def collect(self, vertices, faces, color, anchor, scale, layer):
        self.geometry.append((self.world(vertices, anchor, scale), faces, color))

    def box(self, x, y, z, sx, sy, sz, color):
        v = [(x+i*sx, y+j*sy, z+k*sz) for k in (0, 1) for j in (0, 1) for i in (0, 1)]
        faces = [(0,1,3),(0,3,2),(4,6,7),(4,7,5),(0,4,5),(0,5,1),
                 (2,3,7),(2,7,6),(0,2,6),(0,6,4),(1,5,7),(1,7,3)]
        self.collect(v, faces, color, self.anchor, 1, 0)

    def rod(self, start, end, radius, color):
        core.segment(start, end, radius, radius, color, self.anchor, 1, 0)

    def sphere(self, center, radii, color):
        core.ellipsoid(center, radii, color, self.anchor, 1, 0)

    def cylinder(self, x, y, z, radius, height, color):
        self.rod((x,y,z), (x,y,z+height), radius, color)

    def object(self, obj):
        kind = obj['type']
        self.anchor = np.asarray(obj.get('position', [0,0,0]), float)
        angle = math.radians(obj.get('yaw_degrees', 0))
        self.rotation = np.array([[math.cos(angle),-math.sin(angle),0], [math.sin(angle),math.cos(angle),0], [0,0,1]])
        col = ImageColor.getrgb(obj.get('color', '#937047'))
        if kind == 'segment':
            self.rod(obj['start'], obj['end'], obj['radius'], col)
        elif kind == 'ellipsoid':
            self.sphere([0,0,0], obj['radii'], col)
        elif kind == 'cylinder':
            self.cylinder(0,0,0,obj['radius'],obj['height'],col)
        elif kind == 'stove':
            self.cylinder(0,0,0,.29,.69,(71,72,69))
            self.cylinder(0,0,.63,.31,.035,(118,110,93))
            self.box(-.14,-.294,.21,.27,.025,.19,(37,35,30))
            vessel = obj.get('vessel', 'pan')
            if vessel == 'pan':
                self.sphere([0,0,.78], [.39,.36,.13], (59,59,53))
                self.sphere([0,0,.842], [.33,.30,.027], (100,99,86))
            elif vessel == 'covered_pot':
                self.cylinder(0,0,.70,.32,.22,(158,156,139))
                self.sphere([0,0,.92], [.34,.33,.085], (186,183,165))
                self.rod([-.07,0,1.02],[.07,0,1.02],.025,(57,52,43))
        else:
            sx, sy, sz = obj['size']
            leg = min(.07, sx*.12, sy*.12)
            if kind == 'box':
                self.box(0,0,0,sx,sy,sz,col)
            elif kind in ('table', 'stool', 'shelf'):
                for x in (leg, sx-2*leg):
                    for y in (leg, sy-2*leg):
                        self.box(x,y,0,leg,leg,sz-.04,(105,76,49))
                levels = [sz-.06] if kind != 'shelf' else [sz*.17, sz*.55, sz-.06]
                for z in levels:
                    self.box(0,0,z,sx,sy,.06,col)
                if kind == 'table':
                    for y in np.arange(.10,sy,.19):
                        self.box(.01,y,sz+.001,sx-.02,.007,.002,(110,84,57))
            elif kind == 'sink':
                thick = min(.07, sx*.13, sy*.13, sz*.2)
                self.box(0,0,0,sx,sy,sz-.24 if sz > .3 else sz*.5,col)
                for x in (0,sx-thick):
                    self.box(x,0,sz-.2,thick,sy,.2,col)
                for y in (0,sy-thick):
                    self.box(0,y,sz-.2,sx,thick,.2,col)
                self.box(thick,thick,sz-.21,sx-2*thick,sy-2*thick,.02,(107,113,101))
        self.rotation = np.eye(3)
        self.anchor = np.zeros(3)


def make_geometry(config):
    model = Model()
    core.mesh = model.collect
    core.project = model.world
    floor = config['floor']
    x0,y0,x1,y1 = floor['bounds']
    color = ImageColor.getrgb(floor.get('color', '#b9b5a5'))
    model.box(x0,y0,-.10,x1-x0,y1-y0,.10,tuple(max(c-25,0) for c in color))
    if floor.get('tile_size'):
        sx,sy = floor['tile_size']
        rng = np.random.default_rng(23)
        for row,y in enumerate(np.arange(y0,y1,sy)):
            for x in np.arange(x0-(row%2)*sx/2,x1,sx):
                left,right = max(x,x0), min(x+sx-.018,x1)
                bottom = min(y+sy-.018,y1)
                if right > left and bottom > y:
                    shade = tuple(int(np.clip(c+rng.uniform(-6,6),0,255)) for c in color)
                    model.box(left,y,0,right-left,bottom-y,.016,shade)
    for obj in config.get('objects', []):
        model.object(obj)
    hands = {}
    for p in config['people']:
        angle = math.radians(p.get('yaw_degrees', 0))
        model.rotation = np.array([[math.cos(angle),-math.sin(angle),0], [math.sin(angle),math.cos(angle),0], [0,0,1]])
        hands[p['id']] = core.puppet(p, p['position'], p.get('scale', 1), 0)
    model.rotation = np.eye(3)
    for t in config.get('tools', []):
        model.rod(hands[t['person']][t.get('hand',0)],t['target'],t.get('radius',.012),ImageColor.getrgb(t.get('color','#858577')))
        if t.get('bowl',False):
            model.sphere(t['target'],[.04,.04,.018],(149,149,133))
    return model


def camera(config, geometry):
    settings = config.get('camera', {})
    az = math.radians(settings.get('azimuth_degrees', -60))
    el = math.radians(settings.get('elevation_degrees', 55))
    right = np.array([-math.sin(az),math.cos(az),0])
    up = np.array([-math.cos(az)*math.sin(el),-math.sin(az)*math.sin(el),math.cos(el)])
    toward = np.cross(right, up)
    vertices = np.concatenate([v for v,_,_ in geometry])
    flat = np.stack((vertices@right, -(vertices@up)), axis=-1)
    low, high = flat.min(axis=0), flat.max(axis=0)
    w,h = config.get('canvas', [2048,1536])
    l,t,r,b = config.get('margins', [220,210,260,180])
    scale = min((w-l-r)/(high[0]-low[0]), (h-t-b)/(high[1]-low[1]))
    origin = np.array([l+(w-l-r)/2,t+(h-t-b)/2])-scale*(low+high)/2
    def project(points, anchor, factor):
        q = np.asarray(points)*factor+anchor
        return np.stack((origin[0]+scale*(q@right), origin[1]-scale*(q@up), q@toward),axis=-1)
    return project


def label_image(clean, config, project, font_path):
    image = clean.copy()
    draw = ImageDraw.Draw(image)
    w,h = image.size
    fs = max(17,round(w*.013))
    font = ImageFont.truetype(font_path,fs)
    small = ImageFont.truetype(font_path,max(14,round(fs*.77)))
    title = ImageFont.truetype(font_path,round(fs*1.6))
    draw.text((w*.04,h*.035),config.get('title','人物俯视站位图'),font=title,fill='#292f2e')
    draw.text((w*.04,h*.083),config.get('subtitle','按参考图作近似三维还原的空间示意'),font=small,fill='#6c7069')
    for i,p in enumerate(config['people']):
        z = (1.64-(.43 if p.get('seated',False) else 0))*p.get('scale',1)
        point = np.asarray(p['position'],float)+[0,0,z]
        target = project(point,np.zeros(3),1)[:2]
        name, desc = p.get('name',p['id']),p.get('label','')
        width = max(draw.textbbox((0,0),name,font=font)[2],draw.textbbox((0,0),desc,font=small)[2])+32
        height = fs*3.25 if desc else fs*2
        default = [.03, .18+i*.12] if i%2 == 0 else [.75, .18+i*.12]
        u,v = p.get('label_xy', default)
        x,y = max(0,min(u*w,w-width)), max(0,min(v*h,h-height))
        edge = (x+width,y+height/2) if target[0] > x+width else (x,y+height/2)
        if x <= target[0] <= x+width:
            edge = (target[0],y+height if target[1] > y else y)
        color = p.get('color','#b24b40')
        draw.line([tuple(target),edge],fill=color,width=max(2,w//800))
        draw.rounded_rectangle((x,y,x+width,y+height),radius=10,fill='#fcfaf3',outline='#d7d2c5',width=2)
        draw.rounded_rectangle((x,y,x+5,y+height),radius=2,fill=color)
        draw.text((x+16,y+10),name,font=font,fill='#292e2d')
        if desc:
            draw.text((x+16,y+fs*1.8),desc,font=small,fill='#656c66')
    for n in config.get('notes', []):
        point = project(n['target'],np.zeros(3),1)[:2]
        xy = tuple(np.asarray(n['label_xy'])*[w,h])
        draw.line([xy,tuple(point)],fill='#99988c',width=2)
        draw.text((xy[0]+4,xy[1]-fs),n['text'],font=small,fill='#646b62',stroke_width=2,stroke_fill='#f6f2e7')
    draw.text((w*.04,h*.955),config.get('footer','空间调度示意；外貌与服装以角色参考图为准。'),font=small,fill='#6c7069')
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True,type=Path)
    parser.add_argument('--output-prefix',type=Path)
    parser.add_argument('--clean-only',action='store_true')
    parser.add_argument('--overwrite',action='store_true')
    parser.add_argument('--check-only',action='store_true',help='Validate JSON without rendering or writing files')
    args = parser.parse_args()
    config_path = args.config.expanduser().resolve()
    config = json.loads(config_path.read_text(encoding='utf-8'))
    validate(config)
    if config.get('source_image') and not core.resolve(config_path,config['source_image']).is_file():
        raise ValueError('source_image does not exist; resolve relative to the config file')
    if args.check_only:
        print(json.dumps({'valid':True,'people':len(config['people']),'objects':len(config.get('objects',[]))}))
        return
    prefix = args.output_prefix.expanduser().resolve() if args.output_prefix else core.resolve(config_path,config['output_prefix']).resolve()
    targets = [Path(str(prefix)+'_无字.png')]
    if not args.clean_only:
        targets.append(Path(str(prefix)+'_标注.png'))
    for path in targets:
        if path.exists() and not args.overwrite:
            raise ValueError(str(path)+' already exists; choose a new prefix or explicitly use --overwrite')
    font = None if args.clean_only else core.find_font(config,config_path)
    base_mesh = core.mesh
    model = make_geometry(config)
    project = camera(config,model.geometry)
    core.mesh, core.project = base_mesh, project
    core.W,core.H = map(int,config.get('canvas',[2048,1536]))
    core.SS = int(config.get('supersample',2))
    core.rgb = np.zeros((core.H*core.SS,core.W*core.SS,4),np.uint8)
    core.depth = np.full((core.H*core.SS,core.W*core.SS),-1e9,np.float32)
    for v,faces,color in model.geometry:
        core.mesh(v,faces,color,np.zeros(3),1,0)
    layer = Image.fromarray(core.rgb).resize((core.W,core.H),Image.Resampling.LANCZOS)
    clean = Image.alpha_composite(Image.new('RGBA',(core.W,core.H),config.get('background','#f6f2e7')),layer).convert('RGB')
    labelled = None if args.clean_only else label_image(clean,config,project,font)
    prefix.parent.mkdir(parents=True,exist_ok=True)
    clean.save(targets[0])
    if labelled is not None:
        labelled.save(targets[1])
    print(json.dumps({'size':[core.W,core.H],'people':len(config['people']),'outputs':[str(p) for p in targets]},ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print('Error: '+str(exc),file=sys.stderr)
        sys.exit(2)
