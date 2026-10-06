"""
Validates jump_cuts, chunker, and caption_render using mock word data,
since this sandbox can't reach huggingface.co to download the real
Whisper model. On your machine, main.py will use real transcription.
"""
from moviepy import VideoFileClip
from jump_cuts import apply_jump_cuts
from chunker import build_chunks
from caption_render import render_captions

# Roughly matches the espeak-generated test_input.mp4 timing/content
mock_words = [
    {"word": "This", "start": 0.10, "end": 0.28},
    {"word": "is", "start": 0.28, "end": 0.42},
    {"word": "a", "start": 0.42, "end": 0.48},
    {"word": "quick", "start": 0.48, "end": 0.78},
    {"word": "test", "start": 0.78, "end": 1.05},
    {"word": "of", "start": 1.05, "end": 1.15},
    {"word": "the", "start": 1.15, "end": 1.25},
    {"word": "auto", "start": 1.25, "end": 1.55},
    {"word": "caption", "start": 1.55, "end": 1.95},
    {"word": "system.", "start": 1.95, "end": 2.35},
    # gap here (silence_start 2.91 -> 3.36 in real audio, but we anchor to word times)
    {"word": "Pretty", "start": 3.36, "end": 3.65},
    {"word": "cool", "start": 3.65, "end": 3.95},
    {"word": "right?", "start": 3.95, "end": 4.25},
    # gap here (4.43 -> 4.82)
    {"word": "Let's", "start": 4.82, "end": 5.05},
    {"word": "see", "start": 5.05, "end": 5.25},
    {"word": "how", "start": 5.25, "end": 5.45},
    {"word": "it", "start": 5.45, "end": 5.55},
    {"word": "handles", "start": 5.55, "end": 5.95},
    {"word": "the", "start": 5.95, "end": 6.05},
    {"word": "pop", "start": 6.05, "end": 6.35},
    {"word": "animation", "start": 6.35, "end": 6.95},
    {"word": "and", "start": 6.95, "end": 7.10},
    {"word": "the", "start": 7.10, "end": 7.20},
    {"word": "jump", "start": 7.20, "end": 7.50},
    {"word": "cuts.", "start": 7.50, "end": 7.90},
]

print("[1/3] Testing jump cuts...")
clip = VideoFileClip("samples/test_input.mp4")
print(f"      Original duration: {clip.duration:.2f}s")
new_clip, remapped_words = apply_jump_cuts(clip, mock_words, min_gap=0.45)
print(f"      Duration after jump cuts: {new_clip.duration:.2f}s")
temp_path = "samples/test_cut_temp.mp4"
new_clip.write_videofile(temp_path, codec="libx264", audio_codec="aac", logger=None)
clip.close()
new_clip.close()

print("[2/3] Testing chunker...")
chunks = build_chunks(remapped_words)
for c in chunks:
    print(f"      {c['start']:.2f}-{c['end']:.2f}: {[w['word'] for w in c['words']]}")

print("[3/3] Testing caption rendering...")
render_captions(temp_path, chunks, "output/test_output_mock.mp4")
print("Done -> output/test_output_mock.mp4")
