"""
caption_render.py
Renders TikTok/CapCut-style "pop" captions and burns them onto a video.

Style: 2-3 word chunks, centered, active word scales up + pops with a
spring-ease when it starts being spoken, other words in the chunk stay
smaller/white while the active word can be highlighted in an accent color.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoFileClip, VideoClip, CompositeVideoClip

FONT_PATH = "fonts/LiberationSans-Bold.ttf"
FONT_SIZE = 78
POP_DURATION = 0.12          # seconds for the scale-pop-in animation
POP_OVERSHOOT = 1.25         # how far it overshoots before settling to 1.0
TEXT_COLOR = (255, 255, 255, 255)
ACTIVE_COLOR = (255, 224, 32, 255)   # yellow highlight for the active word
STROKE_COLOR = (0, 0, 0, 255)
STROKE_WIDTH = 6
CAPTION_Y_FRAC = 0.72         # vertical position, fraction of frame height


def ease_out_back(t, overshoot=1.7):
    """Spring-like ease: overshoots past 1.0 then settles. t in [0,1]."""
    c1 = overshoot
    c3 = c1 + 1
    t = max(0.0, min(1.0, t))
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def word_scale_at(word, t_abs):
    """Scale factor for a word at absolute time t_abs (pop-in when it starts)."""
    t_since_start = t_abs - word["start"]
    if t_since_start < 0:
        return 1.0  # not started yet, shouldn't be drawn anyway
    if t_since_start >= POP_DURATION:
        return 1.0
    progress = t_since_start / POP_DURATION
    eased = ease_out_back(progress)
    # eased goes 0 -> ~1.7 -> 1.0 ; map so it visually scales from 0.4 to 1.0 with overshoot
    return 0.5 + 0.5 * eased


def make_caption_frame(chunk, t_abs, frame_size, font, font_active):
    """Render one RGBA frame (transparent bg) with the chunk's words at time t_abs."""
    W, H = frame_size
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    active_idx = None
    for i, w in enumerate(chunk["words"]):
        if w["start"] <= t_abs <= w["end"] + 0.05:
            active_idx = i
            break

    # measure each word to lay them out centered horizontally
    gap = 18
    widths = []
    for i, w in enumerate(chunk["words"]):
        f = font_active if i == active_idx else font
        bbox = draw.textbbox((0, 0), w["word"], font=f, stroke_width=STROKE_WIDTH)
        widths.append(bbox[2] - bbox[0])

    total_width = sum(widths) + gap * (len(widths) - 1)
    x = (W - total_width) / 2
    y_center = int(H * CAPTION_Y_FRAC)

    for i, w in enumerate(chunk["words"]):
        is_active = (i == active_idx)
        f = font_active if is_active else font
        color = ACTIVE_COLOR if is_active else TEXT_COLOR
        scale = word_scale_at(w, t_abs) if is_active else 1.0

        word_img = Image.new("RGBA", (widths[i] + STROKE_WIDTH * 4, FONT_SIZE + STROKE_WIDTH * 4), (0, 0, 0, 0))
        wd = ImageDraw.Draw(word_img)
        wd.text((STROKE_WIDTH * 2, STROKE_WIDTH * 2), w["word"], font=f, fill=color,
                 stroke_width=STROKE_WIDTH, stroke_fill=STROKE_COLOR)

        if scale != 1.0:
            new_w = max(1, int(word_img.width * scale))
            new_h = max(1, int(word_img.height * scale))
            word_img = word_img.resize((new_w, new_h), Image.LANCZOS)

        paste_x = int(x - (word_img.width - widths[i]) / 2)
        paste_y = int(y_center - word_img.height / 2)
        img.alpha_composite(word_img, (paste_x, paste_y))

        x += widths[i] + gap

    return np.array(img)


def render_captions(video_path, chunks, output_path, font_path=FONT_PATH):
    clip = VideoFileClip(video_path)
    W, H = clip.size
    font = ImageFont.truetype(font_path, FONT_SIZE)
    font_active = ImageFont.truetype(font_path, int(FONT_SIZE * 1.05))

    def find_chunk(t):
        for c in chunks:
            if c["start"] <= t <= c["end"]:
                return c
        return None

    _cache = {"t": None, "frame": None}

    def make_frame(t):
        if _cache["t"] == t:
            return _cache["frame"]
        chunk = find_chunk(t)
        if chunk is None:
            frame = np.zeros((H, W, 4), dtype=np.uint8)
        else:
            frame = make_caption_frame(chunk, t, (W, H), font, font_active)
        _cache["t"] = t
        _cache["frame"] = frame
        return frame

    caption_clip = VideoClip(lambda t: make_frame(t)[:, :, :3], duration=clip.duration)
    mask_clip = VideoClip(lambda t: make_frame(t)[:, :, 3] / 255.0, duration=clip.duration, is_mask=True)
    caption_clip = caption_clip.with_mask(mask_clip)

    final = CompositeVideoClip([clip, caption_clip])
    final.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=clip.fps, logger=None)
    clip.close()
    final.close()
