"""Room-scene assets and perspective projection helpers."""
from functools import lru_cache
from io import BytesIO
import urllib.request

from PIL import Image, ImageDraw


ROOM_PHOTO_URLS = {
    "living": "https://images.unsplash.com/photo-1560448204-603b3fc33ddc?auto=format&fit=crop&w=2400&q=90",
    "bedroom": "https://images.unsplash.com/photo-1750271336580-f11df678e840?auto=format&fit=crop&w=2400&q=90",
    "japandi": "https://images.unsplash.com/photo-1534986622832-777a66b043bc?auto=format&fit=crop&w=2400&q=90",
    "modern_bedroom": "https://images.unsplash.com/photo-1546974284-adac38481098?auto=format&fit=crop&w=2400&q=90",
}


@lru_cache(maxsize=4)
def load_room_photo(scene):
    url = ROOM_PHOTO_URLS.get(scene)
    if not url:
        return None
    request = urllib.request.Request(url, headers={"User-Agent": "ArtMockeryLocal/1.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        photo = Image.open(BytesIO(response.read())).convert("RGB")
    return photo


def draw_room_scene(wall, scene):
    """Legacy illustrated-scene fallback; photographic scenes are loaded before artwork compositing."""
    if not scene or scene == "wall":
        return wall
    W, H = wall.size
    d = ImageDraw.Draw(wall)
    floor_y = int(H * .78)
    floor_colors = {"living": (185,149,112), "bedroom": (196,170,138), "japandi": (201,185,158), "modern_bedroom": (159,138,117)}
    d.rectangle((0, floor_y, W, H), fill=floor_colors.get(scene, (185,149,112)))
    d.rectangle((0, floor_y-5, W, floor_y+2), fill=(240,233,220))
    for i in range(1, 9):
        yy = floor_y + i*(H-floor_y)//9
        d.line((0, yy, W, yy), fill=(121,95,69), width=max(1,W//900))
    for i in range(-8, 18):
        xx = i*W//5
        d.line((xx, floor_y, xx+W//7, H), fill=(121,95,69), width=max(1,W//1100))
    # Small room details are scaled relative to the output resolution.
    if scene in ("living", "japandi"):
        sofa = (185,176,159) if scene == "japandi" else (143,154,136)
        cushion = (217,210,197) if scene == "japandi" else (201,197,183)
        d.rounded_rectangle((int(W*.15),int(H*.67),int(W*.85),int(H*.82)), radius=max(8,W//80), fill=sofa)
        d.rectangle((int(W*.18),int(H*.75),int(W*.82),int(H*.84)), fill=sofa)
        d.rounded_rectangle((int(W*.21),int(H*.65),int(W*.79),int(H*.77)), radius=max(8,W//100), fill=sofa)
        for a,b,c in ((.25,.42,cushion),(.44,.60,(156,170,152) if scene=="japandi" else (214,193,166)),(.62,.77,cushion)):
            d.rounded_rectangle((int(W*a),int(H*.66),int(W*b),int(H*.76)), radius=max(5,W//130), fill=c)
        d.rectangle((int(W*.21),int(H*.81),int(W*.235),int(H*.87)), fill=(97,75,54)); d.rectangle((int(W*.76),int(H*.81),int(W*.785),int(H*.87)), fill=(97,75,54))
        # Side table and a leafy plant
        d.ellipse((int(W*.06),int(H*.79),int(W*.18),int(H*.82)), fill=(119,91,61)); d.rectangle((int(W*.115),int(H*.80),int(W*.13),int(H*.88)), fill=(119,91,61))
        d.rectangle((int(W*.88),int(H*.76),int(W*.94),int(H*.87)), fill=(182,127,92))
        for i in range(7):
            x=int(W*(.905+(i%3-1)*.035)); y=int(H*(.74-(i//3)*.035))
            d.line((int(W*.91),int(H*.77),x,y), fill=(82,107,79), width=max(2,W//350))
            d.ellipse((x-int(W*.015),y-int(H*.025),x+int(W*.015),y+int(H*.025)), fill=(113,137,107))
    else:
        headboard=(117,104,94) if scene=="modern_bedroom" else (184,165,143)
        duvet=(222,217,208) if scene=="modern_bedroom" else (238,231,220)
        d.rectangle((int(W*.16),int(H*.57),int(W*.84),int(H*.78)), fill=headboard)
        d.rounded_rectangle((int(W*.13),int(H*.65),int(W*.87),int(H*.86)), radius=max(8,W//90), fill=duvet)
        d.rounded_rectangle((int(W*.16),int(H*.65),int(W*.84),int(H*.81)), radius=max(6,W//100), fill=(174,185,180) if scene=="modern_bedroom" else (215,212,201))
        d.rounded_rectangle((int(W*.22),int(H*.65),int(W*.44),int(H*.72)), radius=max(4,W//150), fill=(247,242,232))
        d.rounded_rectangle((int(W*.47),int(H*.65),int(W*.69),int(H*.72)), radius=max(4,W//150), fill=(247,242,232))
        d.rounded_rectangle((int(W*.16),int(H*.77),int(W*.84),int(H*.84)), radius=max(5,W//120), fill=(137,154,151) if scene=="modern_bedroom" else (183,191,174))
        d.rectangle((int(W*.07),int(H*.72),int(W*.16),int(H*.83)), fill=(139,106,75)); d.rectangle((int(W*.84),int(H*.72),int(W*.93),int(H*.83)), fill=(139,106,75))
    if scene in ("living", "modern_bedroom"):
        d.rounded_rectangle((int(W*.035),int(H*.10),int(W*.155),int(H*.40)), radius=max(2,W//300), fill=(246,240,229))
        d.rectangle((int(W*.047),int(H*.115),int(W*.143),int(H*.385)), fill=(199,214,216))
        d.line((int(W*.095),int(H*.115),int(W*.095),int(H*.385)), fill=(247,240,229), width=max(2,W//150))
        d.line((int(W*.047),int(H*.25),int(W*.143),int(H*.25)), fill=(247,240,229), width=max(2,W//150))
    return wall


def solve_linear_system(matrix, vector):
    """Small Gaussian-elimination solver for an 8x8 projective transform."""
    a = [list(map(float, row)) + [float(value)] for row, value in zip(matrix, vector)]
    n = len(a)
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(a[row][col]))
        if abs(a[pivot][col]) < 1e-12:
            raise ValueError("Degenerate perspective quadrilateral")
        a[col], a[pivot] = a[pivot], a[col]
        div = a[col][col]
        a[col] = [v / div for v in a[col]]
        for row in range(n):
            if row == col:
                continue
            factor = a[row][col]
            if factor:
                a[row] = [v - factor * pivot_v for v, pivot_v in zip(a[row], a[col])]
    return [a[i][-1] for i in range(n)]


def perspective_overlay(source, canvas_size, quad):
    """Project a rectangular frame image onto a room-specific wall quadrilateral."""
    sw, sh = source.size
    # PIL expects output-to-source coefficients. Map the destination quad back to source corners.
    src_points = [(0, 0), (sw, 0), (sw, sh), (0, sh)]
    matrix, values = [], []
    for (x, y), (u, v) in zip(quad, src_points):
        matrix.append([x, y, 1, 0, 0, 0, -u*x, -u*y]); values.append(u)
        matrix.append([0, 0, 0, x, y, 1, -v*x, -v*y]); values.append(v)
    coeff = solve_linear_system(matrix, values)
    return source.transform(canvas_size, Image.Transform.PERSPECTIVE, coeff, Image.Resampling.BICUBIC)


def scene_frame_quad(canvas_size, scene, aspect):
    """Hand-tuned art plane per photo: distinct placement, scale, and camera perspective."""
    W, H = canvas_size
    profiles = {
        # cx, cy, max width, max height, top-left shift, top-right shift, bottom-left shift, bottom-right shift
        "living": (0.50, 0.345, 0.355, 0.445, 0.008, -0.004, -0.010, 0.012),
        "bedroom": (0.505, 0.305, 0.325, 0.405, -0.004, 0.004, 0.002, -0.002),
        "japandi": (0.525, 0.335, 0.335, 0.425, 0.018, -0.018, -0.012, 0.026),
        "modern_bedroom": (0.465, 0.315, 0.325, 0.405, -0.020, 0.012, 0.012, -0.030),
    }
    cx, cy, maxw, maxh, tl, tr, bl, br = profiles.get(scene, profiles["living"])
    w = min(W * maxw, H * maxh * aspect)
    h = w / max(aspect, 0.15)
    if h > H * maxh:
        h = H * maxh; w = h * aspect
    x1, x2 = cx*W-w/2, cx*W+w/2
    y1, y2 = cy*H-h/2, cy*H+h/2
    # Small perspective taper plus a scene-specific lean. Keep shifts proportional to canvas.
    return [(x1+tl*W, y1), (x2+tr*W, y1+H*.004), (x2+br*W, y2), (x1+bl*W, y2-H*.002)]
