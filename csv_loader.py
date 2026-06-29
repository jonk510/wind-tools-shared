"""
Shared CSV loader with BOM stripping and flexible delimiter detection.

load_csv(uploaded_file_or_path)
    Accepts a Streamlit UploadedFile, a file-like object, or a path string.
    Strips UTF-8 BOM, auto-detects delimiter (comma, semicolon, tab).
    Returns a pd.DataFrame.
"""

import io

import pandas as pd


def load_csv(source) -> pd.DataFrame:
    """Load a CSV from a Streamlit UploadedFile, file-like object, or path string.

    Handles UTF-8 BOM and auto-detects comma / semicolon / tab delimiters.
    """
    if isinstance(source, (str, bytes)):
        # Path string or raw bytes
        if isinstance(source, str):
            with open(source, "rb") as fh:
                raw = fh.read()
        else:
            raw = source
    else:
        # Streamlit UploadedFile or file-like
        raw = source.read()
        if hasattr(source, "seek"):
            source.seek(0)

    # Strip UTF-8 BOM if present
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]

    text = raw.decode("utf-8", errors="replace")

    # Detect delimiter from the first non-empty line
    first_line = next((l for l in text.splitlines() if l.strip()), "")
    if "\t" in first_line:
        sep = "\t"
    elif ";" in first_line:
        sep = ";"
    else:
        sep = ","

    return pd.read_csv(io.StringIO(text), sep=sep)
