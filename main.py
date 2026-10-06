"""
main.py
CLI entry point for the reel captioner.

Usage:
  python main.py input.mp4 --output output.mp4
  python main.py input.mp4 --output output.mp4 --no-jump-cuts
  python main.py input.mp4 --output output.mp4 --model small --font fonts/BigShoulders-Bold.ttf
"""
import argparse
import os
import sys

from transcribe import transcribe_video
from chunker import build_chunks
from jump_cuts import apply_jump_cuts
from caption_render import render_captions, FONT_PATH


def main():
    parser = argparse.ArgumentParser(description="Auto-caption a video, TikTok/CapCut pop style, with optional jump cuts.")
    parser.add_argument("input", help="Path to input video file")
    parser.add_argument("--output", default=None, help="Path to output video file")
    parser.add_argument("--model", default="small", help="Whisper model size: tiny/base/small/medium/large-v3")
    parser.add_argument("--font", default=FONT_PATH, help="Path to a .ttf font for captions")
    parser.add_argument("--no-jump-cuts", action="store_true", help="Disable auto jump-cut editing")
    parser.add_argument("--min-gap", type=float, default=0.45, help="Min silence gap (sec) to trigger a jump cut")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Input file not found: {args.input}")
        sys.exit(1)

    output_path = args.output or (os.path.splitext(args.input)[0] + "_captioned.mp4")

    print("[1/4] Transcribing with word-level timestamps...")
    words, info = transcribe_video(args.input, model_size=args.model)
    print(f"      Detected language: {info.language} | {len(words)} words")

    working_video = args.input
    temp_cut_path = None

    if not args.no_jump_cuts:
        print("[2/4] Detecting dead air + applying jump cuts...")
        from moviepy import VideoFileClip
        clip = VideoFileClip(args.input)
        new_clip, words = apply_jump_cuts(clip, words, min_gap=args.min_gap)
        temp_cut_path = os.path.splitext(args.input)[0] + "_cut_temp.mp4"
        new_clip.write_videofile(temp_cut_path, codec="libx264", audio_codec="aac", logger=None)
        clip.close()
        new_clip.close()
        working_video = temp_cut_path
        print(f"      Cut video saved (intermediate): {temp_cut_path}")
    else:
        print("[2/4] Skipping jump cuts (--no-jump-cuts set)")

    print("[3/4] Grouping words into caption chunks...")
    chunks = build_chunks(words)
    print(f"      {len(chunks)} caption chunks created")

    print("[4/4] Rendering pop captions and encoding final video...")
    render_captions(working_video, chunks, output_path, font_path=args.font)

    if temp_cut_path and os.path.exists(temp_cut_path):
        os.remove(temp_cut_path)

    print(f"\nDone! Output saved to: {output_path}")


if __name__ == "__main__":
    main()
