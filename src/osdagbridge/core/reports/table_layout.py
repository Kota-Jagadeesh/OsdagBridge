"""Repeat LaTeX longtable headers without duplicate first-page headings.

This operates on the assembled document, not on engineering calculations.
"""

import re

_START = r"\begin{longtable}"
_END = r"\end{longtable}"
_CAPTION = re.compile(r"\\caption(?:\[[^\]]*\])?\{")


def _balanced_close(text, opening):
    depth = 0
    for index in range(opening, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return index + 1
    return None


def _caption_commands(text):
    """Caption spans, including nested bold commands."""
    for match in _CAPTION.finditer(text):
        opening = match.end() - 1
        finish = _balanced_close(text, opening)
        if finish is not None:
            yield match.start(), finish, text[opening + 1:finish - 1]


def _fix_caption_rows(chunk):
    """Make every longtable caption a complete table row.

    A bare caption followed immediately by hline can be mishandled around
    page transitions. Continuation captions are intentionally unnumbered.
    """
    for start, finish, body in reversed(list(_caption_commands(chunk))):
        before = chunk[start:finish]
        if "(continued)" in body.lower() and not before.startswith(r"\caption[]"):
            before = before.replace(r"\caption{", r"\caption[]{", 1)
        following = chunk[finish:]
        if not following.lstrip().startswith(r"\\"):
            before += r"\\"
        chunk = chunk[:start] + before + chunk[finish:]
    return chunk


def _continuation_title(chunk):
    captions = list(_caption_commands(chunk))
    if not captions:
        return None
    body = captions[0][2]
    if body.startswith(r"\textbf{"):
        body = body[8:-1]
    # Existing original title only, never a fabricated title.
    return body.strip() if body.strip() else None


def _add_header(chunk):
    if r"\endhead" in chunk or r"\endfirsthead" in chunk:
        return chunk
    first = chunk.find(r"\hline")
    second = chunk.find(r"\hline", first + 6) if first >= 0 else -1
    if second < 0:
        return chunk
    header = chunk[first + len(r"\hline"):second]
    if not (0 < len(header) < 1200 and r"\textbf" in header
            and r"\\" in header and r"\multirow" not in header):
        return chunk
    title = _continuation_title(chunk)
    extra = "\n" + r"\endfirsthead" + "\n"
    if title:
        extra += r"\caption[]{\textbf{" + title + " (continued)}}" + r"\\" + "\n"
    extra += r"\hline" + header + r"\hline" + "\n" + r"\endhead"
    return chunk[:second + 6] + extra + chunk[second + 6:]


def repeat_simple_longtable_headers(document):
    """Normalize header blocks and protect the beginning of each longtable.

    Re-running is idempotent. Multirow header layouts are not guessed at.
    Existing firsthead/endhead definitions are preserved.
    """
    pieces = []
    position = 0
    while True:
        start = document.find(_START, position)
        if start == -1:
            pieces.append(document[position:])
            break
        end = document.find(_END, start)
        if end == -1:
            pieces.append(document[position:])
            break
        end += len(_END)
        chunk = document[start:end]
        chunk = _add_header(chunk)
        chunk = _fix_caption_rows(chunk)
        # The check must appear outside longtable, not in an environment hook.
        prefix = document[position:start]
        if not prefix.rstrip().endswith(r"\Needspace{8\baselineskip}"):
            prefix += "\n" + r"\Needspace{8\baselineskip}" + "\n"
        pieces.extend((prefix, chunk))
        position = end
    return "".join(pieces)
