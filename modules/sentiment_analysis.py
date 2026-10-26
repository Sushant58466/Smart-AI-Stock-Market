def classify_text(text):
    """Transparent lexical fallback, not a trained financial language model."""
    positive={"beat","growth","profit","surge","upgrade","strong","gain","record","bullish","positive","rise"}
    negative={"miss","loss","fall","drop","downgrade","weak","decline","bearish","negative","lawsuit","risk"}
    words={w.strip(".,!?():;").lower() for w in text.split()}
    p=len(words&positive); n=len(words&negative)
    score=(p-n)/max(1,p+n)
    label="Positive" if score>.15 else "Negative" if score<-.15 else "Neutral"
    return {"label":label,"score":score,"method":"simple keyword fallback","matched_positive":sorted(words&positive),"matched_negative":sorted(words&negative)}
