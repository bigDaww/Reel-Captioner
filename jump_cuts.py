"""
jump_cuts.py
Auto-generates "quick edit" jump cuts by removing dead-air gaps between
spoken words. Uses the word timestamps we already have from Whisper,
so no separate audio analysis pass is needed.
"""

DEFAULT_MIN_GAP = 0.45   # gaps shorter than this are left alone (natural pauses)
DEFAULT_PADDING = 0.08   # keep a little breathing room around each cut


def compute_keep_segments(words, video_duration, min_gap=DEFAULT_MIN_GAP, padding=DEFAULT_PADDING):
    """
    Returns a list of (start, end) segments to KEEP, with the silent
    gaps between words (longer than min_gap) removed.
    """
    if not words:
        return [(0, video_duration)]

    segments = []
    seg_start = max(0.0, words[0]["start"] - padding)
    prev_end = words[0]["end"]

    for w in words[1:]:
        gap = w["start"] - prev_end
        if gap > min_gap:
            seg_end = min(video_duration, prev_end + padding)
            segments.append((seg_start, seg_end))
            seg_start = max(0.0, w["start"] - padding)
        prev_end = w["end"]

    segments.append((seg_start, min(video_duration, prev_end + padding)))
    return segments


def apply_jump_cuts(video_clip, words, min_gap=DEFAULT_MIN_GAP, padding=DEFAULT_PADDING):
    """
    Takes a moviepy VideoFileClip and word list, returns a new clip with
    dead-air gaps removed (concatenated sub-clips) plus the adjusted
    word timestamps (shifted to match the new, shorter timeline).
    """
    from moviepy import concatenate_videoclips

    segments = compute_keep_segments(words, video_clip.duration, min_gap, padding)
    subclips = [video_clip.subclipped(s, e) for s, e in segments]
    new_clip = concatenate_videoclips(subclips)

    # remap word timestamps onto the new shortened timeline
    remapped = []
    time_cursor = 0.0
    for seg_start, seg_end in segments:
        seg_len = seg_end - seg_start
        for w in words:
            if seg_start <= w["start"] < seg_end:
                shift = time_cursor - seg_start
                remapped.append({
                    "word": w["word"],
                    "start": w["start"] + shift,
                    "end": min(w["end"] + shift, time_cursor + seg_len),
                })
        time_cursor += seg_len

    return new_clip, remapped
