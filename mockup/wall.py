"""Wall material presets, color utilities, and wall image generation."""
from io import BytesIO
import math
import random

from fastapi import HTTPException
from PIL import Image, ImageDraw, ImageEnhance, ImageOps


PRESETS = {
    "warm_plaster": (216, 203, 184), "white_stucco": (233, 231, 223),
    "limewash": (217, 208, 192), "travertine": (211, 193, 165),
    "limestone": (213, 203, 184), "sandstone": (201, 177, 143),
    "clay": (189, 128, 100), "grasscloth": (202, 187, 158),
    "linen": (221, 213, 200), "wood_slats": (189, 149, 104),
    "brick": (184, 120, 94), "marble": (223, 220, 212),
    "microcement": (189, 187, 180), "concrete": (170, 169, 163),
    "sage": (165, 176, 155), "greige": (193, 187, 176),
}


FRAMES = {
    "black": ((36, 35, 33), (76, 74, 70), (23, 23, 22)),
    "white": ((238, 234, 225), (255, 255, 255), (203, 199, 191)),
    "oak": ((199, 162, 116), (225, 197, 155), (169, 132, 86)),
    "walnut": ((105, 70, 47), (138, 97, 66), (73, 48, 33)),
    "gold": ((180, 154, 94), (224, 203, 139), (143, 116, 61)),
}


def parse_hex(value):
    value = str(value or "#d8cbb8").lstrip("#")
    if len(value) != 6:
        return (216, 203, 184)
    try:
        return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return (216, 203, 184)


def blend(a, b, amount):
    amount = max(0.0, min(1.0, amount))
    return tuple(round(x*(1-amount)+y*amount) for x, y in zip(a, b))


def procedural_wall(size, base, intensity, preset="warm_plaster", seed=321):
    """Generate a material-specific wall texture without external image assets."""
    w, h = size
    sw, sh = min(w, 1200), min(h, 1200)
    rng = random.Random(seed)
    img = Image.new("RGB", (sw, sh), base)
    d = ImageDraw.Draw(img, "RGB")
    strength = max(0, min(100, intensity)) / 100
    # Soft broad tonal clouds form the base for plaster, stone and cement.
    pix = img.load()
    for y in range(sh):
        for x in range(sw):
            broad = (math.sin(x/57) + math.sin(y/79) + math.sin((x+y)/131)) * 2.0 * strength
            grain = rng.randint(-10, 10) * strength
            delta = int(broad + grain)
            pix[x, y] = tuple(max(0, min(255, c + delta)) for c in base)
    if preset in ("grasscloth", "linen"):
        step = max(3, min(sw, sh)//(100 if preset == "linen" else 65))
        for y in range(0, sh, step):
            col = tuple(max(0, c-12) for c in base) if (y//step)%2 else tuple(min(255,c+12) for c in base)
            d.line((0,y,sw,y), fill=blend(base,col,0.35*strength), width=1)
        for x in range(0, sw, step):
            col = tuple(max(0, c-15) for c in base) if (x//step)%2 else tuple(min(255,c+10) for c in base)
            d.line((x,0,x,sh), fill=blend(base,col,0.3*strength), width=1)
    elif preset == "wood_slats":
        step = max(24, sw//24)
        for x in range(0, sw, step):
            d.rectangle((x,0,min(sw-1,x+2),sh), fill=blend(base,(83,59,38),0.38*strength))
            d.line((min(sw-1,x+5),0,min(sw-1,x+5),sh), fill=blend(base,(255,225,184),0.3*strength), width=1)
            for y in range(25,sh,95):
                d.line((x+4,y,min(sw-1,x+step-2),min(sh-1,y+20)), fill=blend(base,(100,72,47),0.22*strength), width=1)
    elif preset == "brick":
        bh, bw = max(24, sh//18), max(40, sw//10)
        mortar = blend(base,(235,220,205),0.85)
        for y in range(0,sh,bh):
            d.line((0,y,sw,y),fill=mortar,width=max(1,bh//16))
            offset = bw//2 if (y//bh)%2 else 0
            for x in range(-offset,sw,bw):
                d.line((x,y,x,min(sh,y+bh)),fill=mortar,width=max(1,bw//30))
    elif preset == "travertine":
        for y in range(sh//12,sh,max(12,sh//24)):
            dy = int(math.sin(y/55)*sh*.006)
            col = blend(base,(116,91,62),0.17*strength)
            d.line((0,y+dy,sw,y-dy),fill=col,width=max(1,sh//500))
            d.line((0,y+dy+3,sw,y-dy+3),fill=blend(base,(255,244,220),0.3*strength),width=max(1,sh//600))
        for i in range(max(80,sw//4)):
            x,y=rng.randrange(sw),rng.randrange(sh);r=rng.choice((1,1,2,3))
            d.ellipse((x,y,x+r,y+r),fill=blend(base,(130,108,81),0.18*strength))
    elif preset == "marble":
        for i in range(11):
            x,y=rng.randrange(sw),rng.randrange(sh)
            points=[]
            for j in range(7):
                points.append((max(0,min(sw-1,x+j*sw//18+rng.randint(-sw//25,sw//25))),max(0,min(sh-1,y+j*sh//12+rng.randint(-sh//20,sh//20)))))
            col=blend(base,(126,124,117),0.35*strength)
            d.line(points,fill=col,width=max(1,sw//500))
            d.line([(px+1,py+1) for px,py in points],fill=blend(base,(255,255,250),0.45*strength),width=max(1,sw//700))
    elif preset in ("limestone", "microcement", "concrete"):
        for i in range(max(200,sw//2)):
            x,y=rng.randrange(sw),rng.randrange(sh);r=rng.choice((1,1,2,3,4))
            col=blend(base,(110,106,96) if i%2 else (255,251,240),0.12*strength)
            d.ellipse((x,y,x+r*2,y+r),fill=col)
    else:
        # Limewash and plaster have irregular, overlapping trowel clouds.
        for i in range(max(180,sw//3)):
            x,y=rng.randrange(sw),rng.randrange(sh);rx=rng.randint(max(2,sw//180),max(3,sw//35));ry=max(2,rx//2)
            c=(255,247,230) if i%2 else (112,94,73)
            d.ellipse((x-rx,y-ry,x+rx,y+ry),fill=blend(base,c,0.07*strength))
    return img.resize((w,h), Image.Resampling.BICUBIC)


def make_wall(size, base, tint, texture, wall_bytes=None, preset="warm_plaster"):
    if wall_bytes:
        try:
            source = Image.open(BytesIO(wall_bytes)).convert("RGB")
            source = ImageOps.fit(source, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            wall = source
            if tint > 0:
                color_layer = Image.new("RGB", size, base)
                wall = Image.blend(wall, color_layer, tint/100)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not read wall photo: {exc}")
    else:
        wall = procedural_wall(size, base, texture, preset=preset)
        if tint > 0:
            wall = Image.blend(wall, Image.new("RGB", size, base), tint/100)
    if texture > 0 and wall_bytes:
        # Add restrained monochrome grain over the custom photo.
        grain = Image.effect_noise(size, 18 + texture*0.25).convert("L")
        grain = ImageEnhance.Contrast(grain).enhance(1.25)
        grain_rgb = Image.merge("RGB", (grain, grain, grain))
        wall = Image.blend(wall, grain_rgb, texture/650)
    return wall
