"""High-resolution mockup rendering pipeline."""

from io import BytesIO
import math
import random

from fastapi import HTTPException
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageChops

from .scenes import load_room_photo, perspective_overlay, scene_frame_quad
from .wall import FRAMES, PRESETS, make_wall, parse_hex


# Keep these values synchronized with the finish presets in app.js.
FRAME_FINISHES = {
    "black": ("#242321", "#4c4a46", "#171716"),
    "white": ("#eeeae1", "#ffffff", "#cbc7bf"),
    "oak": ("#c7a274", "#e1c59b", "#a98456"),
    "walnut": ("#69462f", "#8a6142", "#493021"),
    "gold": ("#b49a5e", "#e0cb8b", "#8f743d"),
}


def _hex_rgb(value, fallback="#c7a274"):
    """Convert a hex color to an RGB tuple, with a safe fallback."""
    try:
        return parse_hex(value or fallback)
    except (TypeError, ValueError):
        return parse_hex(fallback)


def _mix_color(color, amount):
    """Match the browser's mixHex behavior."""
    if amount >= 0:
        return tuple(
            round(channel * (1 - amount) + 255 * amount)
            for channel in color
        )

    return tuple(
        round(channel * (1 + amount))
        for channel in color
    )


def _draw_wood_grain(image, strength=45, seed=81427):
    """
    Apply reproducible, subtle wood grain to an RGB frame-face image.

    Grain is drawn horizontally, like the browser preview. The center
    opening is subsequently covered by the recessed edge, mat, and artwork.
    """
    strength = max(0, min(100, float(strength))) / 100

    if strength <= 0:
        return image

    width, height = image.size
    if width < 1 or height < 1:
        return image

    rng = random.Random(seed)

    # Mirrors the browser's grain color and intensity settings.
    base_color = _hex_rgb("#9b704b")
    grain_color = _mix_color(
        _hex_rgb("#c7a274"),
        -0.25 - strength * 0.35,
    )

    # The caller supplies the actual frame base color separately below.
    # This overlay uses white as neutral so multiply only darkens the face.
    overlay = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(overlay)

    intensity = 0.02 + strength * 0.32
    density = 0.5 + strength * 1.5
    line_count = max(12, math.floor(height * 0.32 * density))

    for _ in range(line_count):
        start_y = rng.random() * height
        amplitude = 0.4 + rng.random() * 2.2
        frequency = 0.004 + rng.random() * 0.012
        phase = rng.random() * math.tau
        line_width = max(1, round(0.25 + rng.random() * 1.1))

        points = []
        step = max(2, width // 3000)

        for px in range(0, width + 1, step):
            wave = (
                math.sin(px * frequency + phase) * amplitude
                + math.sin(px * frequency * 0.37 + phase)
                * amplitude
                * 0.6
            )
            py = start_y + wave
            points.append((px, round(py)))

        if len(points) >= 2:
            # Approximate Canvas's translucent multiply composite.
            alpha = intensity * (0.25 + rng.random() * 0.75)
            blend = min(1.0, alpha)
            line_color = tuple(
                round(255 * (1 - blend) + channel * blend)
                for channel in grain_color
            )
            draw.line(points, fill=line_color, width=line_width)

    # Small elongated pores, following the browser's deterministic pattern.
    for _ in range(math.floor(line_count * 0.12)):
        px = round(rng.random() * max(0, width - 1))
        py = round(rng.random() * max(0, height - 1))
        pore_width = max(1, round(3 + rng.random() * 20))
        alpha = intensity * (0.3 + rng.random() * 0.5)
        blend = min(1.0, alpha)

        pore_color = tuple(
            round(255 * (1 - blend) + channel * blend)
            for channel in grain_color
        )

        draw.rectangle(
            (px, py, min(width - 1, px + pore_width), py),
            fill=pore_color,
        )

    # Multiply the grain overlay into the frame base.
    return ImageChops.multiply(image, overlay)


def _draw_wood_grain_on_color(image, base_color, strength=45, seed=81427):
    """
    Apply wood grain using the selected frame color.

    The browser creates a grain overlay with the selected frame color darkened
    according to strength, then composites it with multiply.
    """
    strength = max(0, min(100, float(strength))) / 100

    if strength <= 0:
        return image

    width, height = image.size
    if width < 1 or height < 1:
        return image

    rng = random.Random(seed)

    grain_color = _mix_color(
        base_color,
        -0.25 - strength * 0.35,
    )

    overlay = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(overlay)

    intensity = 0.02 + strength * 0.32
    density = 0.5 + strength * 1.5
    line_count = max(12, math.floor(height * 0.32 * density))
    step = max(2, width // 3000)

    for _ in range(line_count):
        start_y = rng.random() * height
        amplitude = 0.4 + rng.random() * 2.2
        frequency = 0.004 + rng.random() * 0.012
        phase = rng.random() * math.tau
        line_width = max(1, round(0.25 + rng.random() * 1.1))
        alpha = intensity * (0.25 + rng.random() * 0.75)
        blend = min(1.0, alpha)

        line_color = tuple(
            round(255 * (1 - blend) + channel * blend)
            for channel in grain_color
        )

        points = []
        for px in range(0, width + 1, step):
            wave = (
                math.sin(px * frequency + phase) * amplitude
                + math.sin(px * frequency * 0.37 + phase)
                * amplitude
                * 0.6
            )
            points.append((px, round(start_y + wave)))

        if len(points) >= 2:
            draw.line(points, fill=line_color, width=line_width)

    for _ in range(math.floor(line_count * 0.12)):
        px = round(rng.random() * max(0, width - 1))
        py = round(rng.random() * max(0, height - 1))
        pore_width = max(1, round(3 + rng.random() * 20))
        alpha = intensity * (0.3 + rng.random() * 0.5)
        blend = min(1.0, alpha)

        pore_color = tuple(
            round(255 * (1 - blend) + channel * blend)
            for channel in grain_color
        )

        draw.rectangle(
            (px, py, min(width - 1, px + pore_width), py),
            fill=pore_color,
        )

    return ImageChops.multiply(image, overlay)


def render_mockup(painting_bytes, settings, wall_bytes=None):
    try:
        painting = Image.open(BytesIO(painting_bytes))
        painting = ImageOps.exif_transpose(painting).convert("RGB")
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read painting image: {exc}",
        )

    W = max(800, min(6000, int(settings.get("outW", 2400))))
    H = max(800, min(6000, int(settings.get("outH", 2400))))

    frame_style = str(settings.get("frame", "oak"))

    # Select matching defaults when older config files omit frame colors.
    finish = FRAME_FINISHES.get(frame_style, FRAME_FINISHES["oak"])
    default_base = finish[0]
    default_highlight = finish[1]
    default_shadow = finish[2]

    if frame_style == "custom":
        custom_color = settings.get("frameColor", "#c7a274")
        custom_rgb = _hex_rgb(custom_color)
        default_base = custom_color
        default_highlight = "#" + "".join(
            f"{v:02x}" for v in _mix_color(custom_rgb, 0.3)
        )
        default_shadow = "#" + "".join(
            f"{v:02x}" for v in _mix_color(custom_rgb, -0.3)
        )

    custom_frame_rgb = _hex_rgb(
        settings.get("frameColor", default_base),
        default_base,
    )
    frame_highlight_rgb = _hex_rgb(
        settings.get("frameHighlightColor", default_highlight),
        default_highlight,
    )
    frame_shadow_rgb = _hex_rgb(
        settings.get("frameShadowColor", default_shadow),
        default_shadow,
    )

    mat_rgb = _hex_rgb(settings.get("matColor", "#f4f0e7"))

    frame_width_pct = max(
        1, min(9, int(settings.get("frameWidth", 4)))
    )
    mat_pct = max(0, min(18, int(settings.get("matWidth", 8))))
    shadow_pct = max(0, min(100, int(settings.get("shadow", 35))))
    texture = max(0, min(100, int(settings.get("texture", 45))))
    tint = max(0, min(70, int(settings.get("tint", 12))))

    wood_grain_enabled = bool(settings.get("woodGrainEnabled", True))
    wood_grain_strength = max(
        0, min(100, float(settings.get("woodGrainStrength", 45)))
    )

    base = _hex_rgb(settings.get("wallColor", "#d8cbb8"))
    preset = settings.get("preset", "warm_plaster")

    if not settings.get("wallColor") and preset in PRESETS:
        base = PRESETS[preset]

    # The current app.js exports the customizable wall scene.
    scene = str(settings.get("scene", "wall"))
    if scene not in {
        "wall",
        "living",
        "bedroom",
        "japandi",
        "modern_bedroom",
    }:
        scene = "wall"

    art_x_pct = max(-40, min(40, float(settings.get("artX", 0))))
    art_y_pct = max(-40, min(40, float(settings.get("artY", 0))))

    if scene != "wall":
        try:
            photo = load_room_photo(scene)
            if photo is not None:
                wall = ImageOps.fit(
                    photo,
                    (W, H),
                    method=Image.Resampling.LANCZOS,
                    centering=(0.5, 0.5),
                )
            else:
                wall = make_wall(
                    (W, H), base, tint, texture, wall_bytes, preset=preset
                )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Could not load the photographic room scene. "
                    "Check your internet connection and try again. "
                    f"({exc})"
                ),
            )
    else:
        wall = make_wall(
            (W, H), base, tint, texture, wall_bytes, preset=preset
        )

    # Match the browser preview's composition sizing.
    max_art_w = int(W * (0.34 if scene != "wall" else 0.59))
    max_art_h = int(H * (0.43 if scene != "wall" else 0.68))

    orientation = str(settings.get("orientation", "portrait"))
    ratio = 4 / 3 if orientation == "landscape" else 3 / 4

    art_w = min(max_art_w, int(max_art_h * ratio))
    art_h = max(1, int(art_w / ratio))

    if art_h > max_art_h:
        art_h = max_art_h
        art_w = max(1, int(art_h * ratio))

    art_w = max(
        1,
        round(
            art_w
            * max(
                0.25,
                min(1.5, float(settings.get("artWidth", 100)) / 100),
            )
        ),
    )
    art_h = max(
        1,
        round(
            art_h
            * max(
                0.25,
                min(1.5, float(settings.get("artHeight", 100)) / 100),
            )
        ),
    )

    # Match the browser's contain + zoom behavior.
    zoom = max(
        0.7, min(2.0, float(settings.get("artZoom", 100)) / 100)
    )
    scale = min(
        art_w / painting.width,
        art_h / painting.height,
    ) * zoom

    scaled_w = max(1, round(painting.width * scale))
    scaled_h = max(1, round(painting.height * scale))
    resized = painting.resize(
        (scaled_w, scaled_h),
        Image.Resampling.LANCZOS,
    )

    artwork_view = Image.new(
        "RGB", (art_w, art_h), (248, 247, 242)
    )
    paste_x = round((art_w - scaled_w) / 2)
    paste_y = round((art_h - scaled_h) / 2)

    src_left = max(0, -paste_x)
    src_top = max(0, -paste_y)
    src_right = min(scaled_w, art_w - paste_x)
    src_bottom = min(scaled_h, art_h - paste_y)

    if src_right > src_left and src_bottom > src_top:
        crop = resized.crop(
            (src_left, src_top, src_right, src_bottom)
        )
        artwork_view.paste(
            crop,
            (max(0, paste_x), max(0, paste_y)),
        )

    frame_px = (
        0
        if frame_style == "canvas"
        else max(8, round(min(W, H) * frame_width_pct / 100))
    )
    mat_px = (
        0
        if frame_style == "canvas"
        else round(min(art_w, art_h) * mat_pct / 100)
    )

    total_w = art_w + 2 * (frame_px + mat_px)
    total_h = art_h + 2 * (frame_px + mat_px)

    if frame_style != "canvas":
        # Start with the selected base finish.
        frame_rgb = Image.new(
            "RGB", (total_w, total_h), custom_frame_rgb
        )

        # Grain is drawn before the bevel and mat, matching the preview's
        # drawing order. The center will be covered by the inner edge/mat.
        if wood_grain_enabled and wood_grain_strength > 0:
            frame_rgb = _draw_wood_grain_on_color(
                frame_rgb,
                custom_frame_rgb,
                strength=wood_grain_strength,
                seed=81427,
            )

        d = ImageDraw.Draw(frame_rgb)

        # Fine alternating bevel lines around the outer frame face.
        bands = max(1, round(frame_px / 3))
        for i in range(bands):
            right = total_w - 1 - i
            bottom = total_h - 1 - i

            if right <= i or bottom <= i:
                break

            d.rectangle(
                (i, i, right, bottom),
                outline=(
                    frame_shadow_rgb
                    if i % 2 == 0
                    else frame_highlight_rgb
                ),
                width=1,
            )

        # Recessed inner edge, followed by the mat.
        d.rectangle(
            (
                frame_px,
                frame_px,
                total_w - frame_px - 1,
                total_h - frame_px - 1,
            ),
            fill=frame_shadow_rgb,
        )

        if mat_px > 0:
            d.rectangle(
                (
                    frame_px,
                    frame_px,
                    total_w - frame_px - 1,
                    total_h - frame_px - 1,
                ),
                fill=mat_rgb,
            )

        frame_layer = frame_rgb.convert("RGBA")
        ix, iy = frame_px + mat_px, frame_px + mat_px
        frame_layer.paste(artwork_view, (ix, iy))

        # Subtle inner edge around the artwork opening.
        fd = ImageDraw.Draw(frame_layer)
        fd.rectangle(
            (ix - 1, iy - 1, ix + art_w, iy + art_h),
            outline=(65, 60, 53, 255),
            width=max(1, round(frame_px * 0.08)),
        )
    else:
        frame_layer = artwork_view.convert("RGBA")

    if scene != "wall":
        quad = scene_frame_quad(
            (W, H), scene, total_w / total_h
        )
        projected = perspective_overlay(
            frame_layer, (W, H), quad
        )
        alpha = projected.getchannel("A")

        if shadow_pct > 0:
            shadow = Image.new(
                "RGBA", (W, H), (0, 0, 0, 0)
            )
            shadow_alpha = alpha.point(
                lambda v: round(v * shadow_pct / 100 * 0.52)
            )
            shadow.putalpha(shadow_alpha)
            shadow = shadow.filter(
                ImageFilter.GaussianBlur(
                    max(2, round(min(W, H) * 0.012))
                )
            )
            shadow = ImageChops.offset(
                shadow, round(W * 0.006), round(H * 0.012)
            )
            wall = Image.alpha_composite(
                wall.convert("RGBA"), shadow
            )

        wall = Image.alpha_composite(
            wall.convert("RGBA"), projected
        ).convert("RGB")
    else:
        x = round(
            (W - total_w) / 2 + W * art_x_pct / 100
        )
        y = round(
            (H - total_h) / 2 + H * art_y_pct / 100
        )

        if shadow_pct > 0:
            shadow_layer = Image.new(
                "RGBA", (W, H), (0, 0, 0, 0)
            )
            sd = ImageDraw.Draw(shadow_layer)
            offset = max(2, round(min(W, H) * 0.012))

            sd.rectangle(
                (
                    x + offset,
                    y + offset,
                    x + total_w + offset,
                    y + total_h + offset,
                ),
                fill=(0, 0, 0, round(shadow_pct * 1.05)),
            )

            shadow_layer = shadow_layer.filter(
                ImageFilter.GaussianBlur(
                    max(2, round(min(W, H) * 0.018))
                )
            )
            wall = Image.alpha_composite(
                wall.convert("RGBA"), shadow_layer
            ).convert("RGB")

        wall.paste(frame_layer.convert("RGB"), (x, y))

    out = BytesIO()
    fmt = str(settings.get("format", "PNG")).upper()

    if fmt == "JPEG":
        wall.save(out, format="JPEG", quality=94, optimize=True)
        media_type = "image/jpeg"
    else:
        wall.save(out, format="PNG", optimize=True)
        media_type = "image/png"

    return out.getvalue(), media_type
