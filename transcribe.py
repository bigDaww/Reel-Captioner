"""
transcribe.py
Transcribes a video/audio file and returns word-level timestamps
using faster-whisper.
"""
from faster_whisper import WhisperModel


def transcribe_video(path, model_size="small", device="cpu", compute_type="int8"):
    """
    Returns a list of word dicts: [{"word": str, "start": float, "end": float}, ...]
    Times are in seconds.
    """
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    segments, info = model.transcribe(
        path,
        word_timestamps=True,
        vad_filter=True,          # skips silence, improves accuracy
        vad_parameters=dict(min_silence_duration_ms=300),
    )

    words = []
    for segment in segments:
        if segment.words is None:
            continue
        for w in segment.words:
            words.append({
                "word": w.word.strip(),
                "start": w.start,
                "end": w.end,
                "prob": w.probability,
            })

    return words, info


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <video_path>")
        sys.exit(1)

    words, info = transcribe_video(sys.argv[1])
    print(f"Detected language: {info.language} (p={info.language_probability:.2f})")
    print(json.dumps(words, indent=2))
