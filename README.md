# Reel Captioner

Auto-generates TikTok/CapCut-style "pop" captions for short video clips, with
optional automatic jump cuts (dead-air removal).

## Setup

```bash
pip install -r requirements.txt
```

Requires `ffmpeg` installed on your system (`ffmpeg -version` to check).

The first run will download a Whisper model from Hugging Face (needs internet
access once — cached locally after that).

## Usage

```bash
python main.py your_clip.mp4
```

This outputs `your_clip_captioned.mp4` in the same folder.

### Options

```bash
python main.py your_clip.mp4 --output final.mp4
python main.py your_clip.mp4 --no-jump-cuts              # keep original pacing, captions only
python main.py your_clip.mp4 --model medium               # more accurate transcription (slower)
python main.py your_clip.mp4 --min-gap 0.6                # only cut silences longer than 0.6s
python main.py your_clip.mp4 --font fonts/BigShoulders-Bold.ttf   # different caption font
```

Whisper model sizes (accuracy vs speed): `tiny`, `base`, `small` (default),
`medium`, `large-v3`. Start with `small` — it's a good balance for short clips.

## How it works

1. **transcribe.py** — runs faster-whisper to get word-level timestamps
2. **jump_cuts.py** — finds silence gaps longer than `--min-gap` seconds
   between words and cuts them out, then remaps word timestamps to the new
   shortened timeline
3. **chunker.py** — groups words into 2-3 word caption chunks (splits on
   sentence punctuation, long pauses, or length limits)
4. **caption_render.py** — draws each caption frame-by-frame with PIL: the
   word currently being spoken scales in with a spring/overshoot animation
   (ease-out-back) and is highlighted in yellow; other words in the chunk
   stay white. Frames are composited onto the video via moviepy.

## Tuning the look

Open `caption_render.py` and adjust:
- `FONT_SIZE` — caption text size
- `POP_DURATION` — how fast the pop-in animation plays (seconds)
- `ACTIVE_COLOR` — highlight color for the word being spoken
- `CAPTION_Y_FRAC` — vertical position (0.72 = lower-third, reel style)
- `fonts/BigShoulders-Bold.ttf` is included as a punchier display-font
  alternative to the default Liberation Sans Bold

Open `chunker.py` and adjust:
- `MAX_WORDS_PER_CHUNK` — how many words appear together (2-3 is the classic look)
- `MAX_GAP_SECONDS` — pause length that forces a new caption chunk

Open `jump_cuts.py` and adjust:
- `DEFAULT_MIN_GAP` — minimum silence length that gets cut
- `DEFAULT_PADDING` — breathing room kept around each cut

## Notes

- Tested end-to-end with a synthetic clip (silence detection, chunking,
  and pop-animation rendering all verified working).
- For a 40 second clip, expect the `small` model to transcribe in well
  under 30 seconds on CPU; `medium`/`large-v3` will be slower but more
  accurate, especially with background music or accents.
- If you want captions burned onto vertical (9:16) reels specifically,
  just feed in a vertical source clip — the renderer adapts to whatever
  resolution the input video is.
