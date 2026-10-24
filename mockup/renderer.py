"""High-resolution mockup rendering pipeline."""

from io import BytesIO

from fastapi import HTTPException
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageChops

from .scenes import load_room_photo, perspective_overlay, scene_frame_quad
from .wall import FRAMES, PRESETS, make_wall, parse_hex


def render_mockup(painting_bytes, settings, wall_bytes=None):
    try:
        painting = Image.open(BytesIO(painting_bytes))
        painting = ImageOps.exif_transpose(painting).convert("RGB")
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Could not read painting image: {exc}"
        )

    W = max(800, min(6000, int(settings.get("outW", 2400))))
    H = max(800, min(6000, int(settings.get("outH", 2400))))
    frame_style = str(settings.get("frame", "oak"))
    custom_frame_rgb = parse_hex(settings.get("frameColor", "#c7a274"))
    frame_highlight_rgb = parse_hex(settings.get("frameHighlightColor", "#e1c59b"))
    frame_shadow_rgb = parse_hex(settings.get("frameShadowColor", "#a98456"))
    mat_rgb = parse_hex(settings.get("matColor", "#f4f0e7"))
    frame_width_pct = max(1, min(9, int(settings.get("frameWidth", 4))))
    mat_pct = max(0, min(18, int(settings.get("matWidth", 8))))
    shadow_pct = max(0, min(100, int(settings.get("shadow", 35))))
    texture = max(0, min(100, int(settings.get("texture", 45))))
    tint = max(0, min(70, int(settings.get("tint", 12))))
    base = parse_hex(settings.get("wallColor", "#d8cbb8"))
    preset = settings.get("preset", "warm_plaster")
    if not settings.get("wallColor") and preset in PRESETS:
        base = PRESETS[preset]

    scene = "wall"
    art_x_pct = max(-40, min(40, float(settings.get("artX", 0))))
    art_y_pct = max(-40, min(40, float(settings.get("artY", 0))))
    if scene != "wall":
        try:
            photo = load_room_photo(scene)
            if photo is not None:
                wall = ImageOps.fit(
                    photo, (W, H), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5)
                )
            else:
                wall = make_wall((W, H), base, tint, texture, wall_bytes, preset=preset)
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Could not load the photographic room scene. Check your internet connection and try again. ({exc})",
            )
    else:
        wall = make_wall((W, H), base, tint, texture, wall_bytes, preset=preset)
    # Build the frame as its own layer so room scenes can project it onto a wall plane.
    # Keep export geometry in sync with the 900x900 browser preview. The
    # preview uses the selected orientation (not the uploaded file's aspect
    # ratio) to size the frame opening, then fits/crops the image inside it.
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
        round(art_w * max(0.25, min(1.5, float(settings.get("artWidth", 100)) / 100))),
    )
    art_h = max(
        1,
        round(art_h * max(0.25, min(1.5, float(settings.get("artHeight", 100)) / 100))),
    )
    # Match Canvas drawImage(..., contain + zoom) behavior in the preview.
    zoom = max(0.7, min(2.0, float(settings.get("artZoom", 100)) / 100))
    scale = min(art_w / painting.width, art_h / painting.height) * zoom
    scaled_w = max(1, round(painting.width * scale))
    scaled_h = max(1, round(painting.height * scale))
    resized = painting.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
    artwork_view = Image.new("RGB", (art_w, art_h), (248, 247, 242))
    paste_x = round((art_w - scaled_w) / 2)
    paste_y = round((art_h - scaled_h) / 2)
    # Crop to the fixed frame opening when zoomed in; otherwise leave the
    # neutral backing visible where the uploaded artwork doesn't fill it.
    src_left = max(0, -paste_x)
    src_top = max(0, -paste_y)
    src_right = min(scaled_w, art_w - paste_x)
    src_bottom = min(scaled_h, art_h - paste_y)
    if src_right > src_left and src_bottom > src_top:
        crop = resized.crop((src_left, src_top, src_right, src_bottom))
        artwork_view.paste(crop, (max(0, paste_x), max(0, paste_y)))

    frame_px = (
        0
        if frame_style == "canvas"
        else max(8, round(min(W, H) * frame_width_pct / 100))
    )
    mat_px = 0 if frame_style == "canvas" else round(min(art_w, art_h) * mat_pct / 100)
    total_w, total_h = art_w + 2 * (frame_px + mat_px), art_h + 2 * (frame_px + mat_px)
    frame_layer = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
    if frame_style != "canvas":
        if frame_style == "custom":
            c0 = custom_frame_rgb
            c1 = tuple(round(v * 0.7 + 255 * 0.3) for v in c0)
            c2 = tuple(round(v * 0.7) for v in c0)
        else:
            c0, c1, c2 = FRAMES.get(frame_style, FRAMES["oak"])

        # Match the browser preview's frame face and fine bevel outlines.
        frame_rgb = Image.new("RGB", (total_w, total_h), c0)
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
                outline=frame_shadow_rgb if i % 2 == 0 else frame_highlight_rgb,
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
        quad = scene_frame_quad((W, H), scene, total_w / total_h)
        projected = perspective_overlay(frame_layer, (W, H), quad)
        alpha = projected.getchannel("A")
        if shadow_pct > 0:
            shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            shadow_alpha = alpha.point(lambda v: round(v * shadow_pct / 100 * 0.52))
            shadow.putalpha(shadow_alpha)
            shadow = shadow.filter(
                ImageFilter.GaussianBlur(max(2, round(min(W, H) * 0.012)))
            )
            shadow = ImageChops.offset(shadow, round(W * 0.006), round(H * 0.012))
            wall = Image.alpha_composite(wall.convert("RGBA"), shadow)
        wall = Image.alpha_composite(wall.convert("RGBA"), projected).convert("RGB")
    else:
        x, y = round((W - total_w) / 2 + W * art_x_pct / 100), round(
            (H - total_h) / 2 + H * art_y_pct / 100
        )
        if shadow_pct > 0:
            shadow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(shadow_layer)
            offset = max(2, round(min(W, H) * 0.012))
            sd.rectangle(
                (x + offset, y + offset, x + total_w + offset, y + total_h + offset),
                fill=(0, 0, 0, round(shadow_pct * 1.05)),
            )
            shadow_layer = shadow_layer.filter(
                ImageFilter.GaussianBlur(max(2, round(min(W, H) * 0.018)))
            )
            wall = Image.alpha_composite(wall.convert("RGBA"), shadow_layer).convert(
                "RGB"
            )
        wall.paste(frame_layer.convert("RGB"), (x, y))
    # Room scenes are photographs; keep the background behind the framed artwork.
    out = BytesIO()
    fmt = str(settings.get("format", "PNG")).upper()
    if fmt == "JPEG":
        wall.save(out, format="JPEG", quality=94, optimize=True)
        media_type = "image/jpeg"
    else:
        wall.save(out, format="PNG", optimize=True)
        media_type = "image/png"
    return out.getvalue(), media_type
