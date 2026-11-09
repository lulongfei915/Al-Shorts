"""Use the scene-mannequin-blocking renderer, with a plain cloth-bag prop.

Run with the bundled Python interpreter and --config <JSON path>.
"""
import importlib.util
from pathlib import Path

workspace = Path(__file__).resolve().parents[3]
renderer_path = workspace / '.agents/skills/scene-mannequin-blocking/scripts/render_mannequins.py'
spec = importlib.util.spec_from_file_location('scene_mannequin_renderer', renderer_path)
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)
base_puppet = renderer.puppet


def puppet_with_cloth_bag(person, anchor, scale, layer):
    hands = base_puppet(person, anchor, scale, layer)
    if not person.get('cloth_bag'):
        return hands
    hand = person['arms'][1][2]
    mirror = 1 if person.get('facing', 'left') == 'left' else -1
    hx, hy, hz = hand
    hx *= mirror
    color = (85, 111, 129)
    # Tapered fabric bag. Handles meet the carrying hand, without vegetables
    # protruding from the bag or borrowing another family's food props.
    vertices = []
    for x, y, z in [
        (-.15, -.065, -.43), (.15, -.065, -.43),
        (.125, -.065, -.18), (-.125, -.065, -.18),
        (-.15, .065, -.43), (.15, .065, -.43),
        (.125, .065, -.18), (-.125, .065, -.18),
    ]:
        vertices.append([hx+x, hy+y, hz+z])
    faces = [(0, 1, 2), (0, 2, 3), (4, 7, 6), (4, 6, 5),
             (0, 4, 5), (0, 5, 1), (1, 5, 6), (1, 6, 2),
             (3, 2, 6), (3, 6, 7), (0, 3, 7), (0, 7, 4)]
    renderer.mesh(vertices, faces, color, anchor, scale, layer)
    for side in (-1, 1):
        a = [hx-.10, hy+side*.052, hz-.18]
        b = [hx-.065, hy+side*.025, hz-.045]
        c = [hx+.065, hy+side*.025, hz-.045]
        d = [hx+.10, hy+side*.052, hz-.18]
        for start, end in ((a, b), (b, c), (c, d)):
            renderer.segment(start, end, .010, .010, color, anchor, scale, layer)
    return hands


renderer.puppet = puppet_with_cloth_bag

if __name__ == '__main__':
    renderer.main()
