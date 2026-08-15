from __future__ import annotations

import math
import os
import time
from pathlib import Path

LEFT_SINGLE_CURLY_QUOTE = "‘"
RIGHT_SINGLE_CURLY_QUOTE = "’"
LEFT_DOUBLE_CURLY_QUOTE = "“"
RIGHT_DOUBLE_CURLY_QUOTE = "”"

MAX_EDIT_FILE_SIZE = 1024 * 1024 * 1024

FILE_NOT_FOUND_CWD_NOTE = "Note: your current working directory is"

_HEAD_SAMPLE = 4096


class EditNotApplied(RuntimeError):
    pass


def normalize_quotes(text: str) -> str:
    return (
        text.replace(LEFT_SINGLE_CURLY_QUOTE, "'")
        .replace(RIGHT_SINGLE_CURLY_QUOTE, "'")
        .replace(LEFT_DOUBLE_CURLY_QUOTE, '"')
        .replace(RIGHT_DOUBLE_CURLY_QUOTE, '"')
    )


def find_actual_string(file_content: str, search_string: str) -> str | None:
    if search_string in file_content:
        return search_string

    index = normalize_quotes(file_content).find(normalize_quotes(search_string))
    if index == -1:
        return None
    return file_content[index : index + len(search_string)]


def _is_opening_context(chars: str, index: int) -> bool:
    if index == 0:
        return True
    prev = chars[index - 1]
    return prev in (" ", "\t", "\n", "\r", "(", "[", "{", "—", "–")


def _apply_curly_double_quotes(text: str) -> str:
    out: list[str] = []
    for i, ch in enumerate(text):
        if ch == '"':
            out.append(
                LEFT_DOUBLE_CURLY_QUOTE
                if _is_opening_context(text, i)
                else RIGHT_DOUBLE_CURLY_QUOTE
            )
        else:
            out.append(ch)
    return "".join(out)


def _apply_curly_single_quotes(text: str) -> str:
    out: list[str] = []
    for i, ch in enumerate(text):
        if ch != "'":
            out.append(ch)
            continue
        prev = text[i - 1] if i > 0 else None
        nxt = text[i + 1] if i < len(text) - 1 else None
        if prev is not None and prev.isalpha() and nxt is not None and nxt.isalpha():
            out.append(RIGHT_SINGLE_CURLY_QUOTE)
        else:
            out.append(
                LEFT_SINGLE_CURLY_QUOTE
                if _is_opening_context(text, i)
                else RIGHT_SINGLE_CURLY_QUOTE
            )
    return "".join(out)


def preserve_quote_style(old_string: str, actual_old_string: str, new_string: str) -> str:
    if old_string == actual_old_string:
        return new_string

    has_double = (
        LEFT_DOUBLE_CURLY_QUOTE in actual_old_string
        or RIGHT_DOUBLE_CURLY_QUOTE in actual_old_string
    )
    has_single = (
        LEFT_SINGLE_CURLY_QUOTE in actual_old_string
        or RIGHT_SINGLE_CURLY_QUOTE in actual_old_string
    )
    if not has_double and not has_single:
        return new_string

    result = new_string
    if has_double:
        result = _apply_curly_double_quotes(result)
    if has_single:
        result = _apply_curly_single_quotes(result)
    return result


def apply_edit_to_file(
    original_content: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> str:
    count = -1 if replace_all else 1

    if new_string != "":
        return original_content.replace(old_string, new_string, count)

    strip_trailing_newline = not old_string.endswith("\n") and (
        old_string + "\n"
    ) in original_content
    if strip_trailing_newline:
        return original_content.replace(old_string + "\n", "", count)
    return original_content.replace(old_string, "", count)


def apply_edit(
    file_contents: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> str:
    if not file_contents and old_string == "" and new_string == "":
        return ""

    updated = (
        new_string
        if old_string == ""
        else apply_edit_to_file(file_contents, old_string, new_string, replace_all)
    )
    if updated == file_contents:
        raise EditNotApplied("String not found in file. Failed to apply edit.")
    return updated


def detect_encoding(head: bytes) -> str:
    if len(head) == 0:
        return "utf-8"
    if len(head) >= 2 and head[0] == 0xFF and head[1] == 0xFE:
        return "utf-16-le"
    return "utf-8"


def detect_line_endings(content: str) -> str:
    crlf = 0
    lf = 0
    for i, ch in enumerate(content):
        if ch != "\n":
            continue
        if i > 0 and content[i - 1] == "\r":
            crlf += 1
        else:
            lf += 1
    return "CRLF" if crlf > lf else "LF"


def read_file_with_metadata(path: Path) -> tuple[str, str, str]:
    raw = path.read_bytes()
    encoding = detect_encoding(raw[:_HEAD_SAMPLE])
    text = raw.decode(encoding)
    line_endings = detect_line_endings(text[:_HEAD_SAMPLE])
    return text.replace("\r\n", "\n"), encoding, line_endings


def write_text_content(path: Path, content: str, encoding: str, endings: str) -> None:
    to_write = content
    if endings == "CRLF":
        to_write = content.replace("\r\n", "\n").replace("\n", "\r\n")
    _write_atomic(path, to_write.encode(encoding))


def _write_atomic(path: Path, payload: bytes) -> None:
    target = path
    try:
        link = os.readlink(path)
        target = Path(link) if os.path.isabs(link) else Path(os.path.dirname(path)) / link
    except OSError:
        pass

    temp = target.with_name(f"{target.name}.tmp.{os.getpid()}.{int(time.time() * 1000)}")

    target_mode: int | None = None
    try:
        target_mode = target.stat().st_mode
    except FileNotFoundError:
        target_mode = None

    try:
        with open(temp, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if target_mode is not None:
            os.chmod(temp, target_mode)
        os.replace(temp, target)
    except OSError:
        try:
            temp.unlink()
        except OSError:
            pass
        with open(target, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())


def format_file_size(size_in_bytes: int) -> str:
    kb = size_in_bytes / 1024
    if kb < 1:
        return f"{size_in_bytes} bytes"
    if kb < 1024:
        return f"{_fixed1(kb)}KB"
    mb = kb / 1024
    if mb < 1024:
        return f"{_fixed1(mb)}MB"
    return f"{_fixed1(mb / 1024)}GB"


def _fixed1(value: float) -> str:
    text = f"{math.floor(value * 10 + 0.5) / 10:.1f}"
    return text.removesuffix(".0")


def find_similar_file(path: Path) -> str | None:
    try:
        entries = os.listdir(path.parent)
    except OSError:
        return None
    for name in entries:
        candidate = path.parent / name
        if candidate.stem == path.stem and candidate != path:
            return name
    return None


def suggest_path_under_cwd(requested_path: str, cwd: str) -> str | None:
    cwd_parent = os.path.dirname(cwd)

    parent = os.path.dirname(requested_path)
    if os.path.isdir(parent):
        resolved = os.path.join(os.path.realpath(parent), os.path.basename(requested_path))
    else:
        resolved = requested_path

    prefix = cwd_parent if cwd_parent == os.sep else cwd_parent + os.sep
    if (
        not resolved.startswith(prefix)
        or resolved.startswith(cwd + os.sep)
        or resolved == cwd
    ):
        return None

    corrected = os.path.join(cwd, os.path.relpath(resolved, cwd_parent))
    return corrected if os.path.exists(corrected) else None


def is_unc_path(file_path: str) -> bool:
    return file_path.startswith(("\\\\", "//"))
