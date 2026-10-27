"""Wall material presets, color utilities, and wall image generation."""

from io import BytesIO
from PIL import Image, ImageFilter

from fastapi import HTTPException
from PIL import Image, ImageDraw, ImageEnhance, ImageOps

PRESETS = {
    "warm_plaster": (216, 203, 184),
    "white_stucco": (233, 231, 223),
    "limewash": (217, 208, 192),
    "travertine": (211, 193, 165),
    "limestone": (213, 203, 184),
    "sandstone": (201, 177, 143),
    "clay": (189, 128, 100),
    "grasscloth": (202, 187, 158),
    "linen": (221, 213, 200),
    "wood_slats": (189, 149, 104),
    "brick": (184, 120, 94),
    "marble": (223, 220, 212),
    "microcement": (189, 187, 180),
    "concrete": (170, 169, 163),
    "sage": (165, 176, 155),
    "greige": (193, 187, 176),
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
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return (216, 203, 184)


def blend(a, b, amount):
    amount = max(0.0, min(1.0, amount))
    return tuple(round(x * (1 - amount) + y * amount) for x, y in zip(a, b))


def procedural_wall(size, base, texture, preset="warm_plaster"):
    import random
    from PIL import Image, ImageFilter

    width, height = size
    strength = max(0.0, min(100.0, float(texture))) / 100.0

    wall = Image.new("RGB", size, base)

    if strength <= 0:
        return wall

    rng = random.Random(81427)

    def noise_layer(cell_size, blur_radius):
        small_w = max(2, (width + cell_size - 1) // cell_size)
        small_h = max(2, (height + cell_size - 1) // cell_size)

        noise = Image.new("L", (small_w, small_h))
        noise.putdata([
            rng.randint(80, 176)
            for _ in range(small_w * small_h)
        ])

        noise = noise.resize(size, Image.Resampling.BICUBIC)

        if blur_radius > 0:
            noise = noise.filter(
                ImageFilter.GaussianBlur(blur_radius)
            )

        return noise

    short_side = min(width, height)

    # Broad, irregular tonal variation.
    broad = noise_layer(
        max(12, short_side // 20),
        max(2, short_side // 45)
    )

    # Fine plaster variation.
    medium = noise_layer(
        max(3, short_side // 100),
        max(1, short_side // 400)
    )

    # Combine the scales and pull the result toward neutral gray.
    texture_map = Image.blend(broad, medium, 0.55)
    neutral = Image.new("L", size, 128)
    texture_map = Image.blend(
        neutral,
        texture_map,
        0.35 + strength * 0.25
    )

    # Apply subtle, consistent luminance variation to the wall.
    texture_rgb = Image.merge(
        "RGB",
        (texture_map, texture_map, texture_map)
    )

    wall = Image.blend(
        wall,
        texture_rgb,
        0.035 + strength * 0.045
    )

    return wall


def make_wall(size, base, tint, texture, wall_bytes=None, preset="warm_plaster"):
    if wall_bytes:
        try:
            source = Image.open(BytesIO(wall_bytes)).convert("RGB")
            source = ImageOps.fit(
                source, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5)
            )
            wall = source
            if tint > 0:
                color_layer = Image.new("RGB", size, base)
                wall = Image.blend(wall, color_layer, tint / 100)
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail=f"Could not read wall photo: {exc}"
            )
    else:
        wall = procedural_wall(size, base, texture, preset=preset)
        if tint > 0:
            wall = Image.blend(wall, Image.new("RGB", size, base), tint / 100)
    if texture > 0 and wall_bytes:
        # Add restrained monochrome grain over the custom photo.
        grain = Image.effect_noise(size, 18 + texture * 0.25).convert("L")
        grain = ImageEnhance.Contrast(grain).enhance(1.25)
        grain_rgb = Image.merge("RGB", (grain, grain, grain))
        wall = Image.blend(wall, grain_rgb, texture / 650)
    return wall
