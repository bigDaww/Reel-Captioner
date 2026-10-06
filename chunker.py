"""
chunker.py
Groups word-level timestamps into short on-screen caption chunks
(2-4 words at a time), TikTok/CapCut style.
"""

MAX_WORDS_PER_CHUNK = 3
MAX_CHARS_PER_CHUNK = 20
MAX_GAP_SECONDS = 0.6  # if silence gap exceeds this, force a new chunk


def build_chunks(words, max_words=MAX_WORDS_PER_CHUNK, max_chars=MAX_CHARS_PER_CHUNK):
    """
    Input: list of {"word","start","end"} dicts from transcribe.py
    Output: list of chunks, each:
      {
        "start": float, "end": float,
        "words": [{"word","start","end"}, ...]
      }
    Each chunk is a small group of words shown together, with each
    word's own start/end preserved so the renderer knows which word
    is "active" (being spoken) at any timestamp.
    """
    chunks = []
    current = []
    current_chars = 0

    def flush():
        nonlocal current, current_chars
        if current:
            chunks.append({
                "start": current[0]["start"],
                "end": current[-1]["end"],
                "words": current,
            })
        current = []
        current_chars = 0

    prev_end = None
    for w in words:
        word_text = w["word"]
        if not word_text:
            continue

        gap = (w["start"] - prev_end) if prev_end is not None else 0
        would_exceed_words = len(current) >= max_words
        would_exceed_chars = current_chars + len(word_text) + 1 > max_chars
        big_gap = gap > MAX_GAP_SECONDS
        ends_sentence = prev_end is not None and current and current[-1]["word"].endswith((".", "!", "?"))

        if current and (would_exceed_words or would_exceed_chars or big_gap or ends_sentence):
            flush()

        current.append(w)
        current_chars += len(word_text) + 1
        prev_end = w["end"]

    flush()
    return chunks


if __name__ == "__main__":
    # quick smoke test with fake data
    fake_words = [
        {"word": "This", "start": 0.0, "end": 0.2},
        {"word": "is", "start": 0.2, "end": 0.3},
        {"word": "a", "start": 0.3, "end": 0.35},
        {"word": "test", "start": 0.35, "end": 0.6},
        {"word": "of", "start": 0.6, "end": 0.7},
        {"word": "the", "start": 0.7, "end": 0.8},
        {"word": "caption", "start": 0.8, "end": 1.2},
        {"word": "system.", "start": 1.2, "end": 1.6},
        {"word": "Pretty", "start": 2.3, "end": 2.6},
        {"word": "cool", "start": 2.6, "end": 2.9},
        {"word": "right?", "start": 2.9, "end": 3.2},
    ]
    for c in build_chunks(fake_words):
        print(c["start"], c["end"], [w["word"] for w in c["words"]])
