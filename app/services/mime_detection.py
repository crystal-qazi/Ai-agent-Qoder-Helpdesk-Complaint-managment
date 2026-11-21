"""MIME-type detection with a graceful fallback when libmagic is absent.

On Linux the application requires the ``libmagic`` shared library
(``python-magic`` is only pulled in for that platform).  On any other
platform the C extension of ``python-magic`` may fail to load at import
time, so we try it lazily and fall back to a small header-based
sniffer that covers the extensions the application accepts.
"""
from typing import Optional, Tuple


# The Python ``magic`` C extension probes ``find_library`` on import,
# which on Windows walks the entire ``PATH`` environment.  On hosts
# where PATH points at a network drive that is currently offline or
# unreachable the call can block for minutes.  We disable the
# import-time probe so the app fails fast and falls through to the
# header sniffer when libmagic is not installed.
def _safe_import_magic():
    import magic as _magic_mod
    return _magic_mod


try:
    import ctypes.util as _ctypes_util
    _orig_find_library = _ctypes_util.find_library
    _ctypes_util.find_library = lambda *_a, **_k: None
    _MAGIC_MODULE = _safe_import_magic()
except Exception:
    _MAGIC_MODULE = None
finally:
    if _orig_find_library is not None:
        _ctypes_util.find_library = _orig_find_library


# Signature bytes (first N) -> canonical MIME type.  Ordered so the
# more specific match wins (``application/zip`` must be checked before
# ``application/x-zip-compressed``-style entries, etc.).  Each entry
# lists the magic bytes that identify the file, followed by the MIME
# string to return.
_SIGNATURES = (
    (b'%PDF', 'application/pdf'),
    (b'PK\x03\x04', 'application/vnd.openxmlformats-officedocument'),
    (b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',
     'application/vnd.ms-excel'),
    (b'GIF8', 'image/gif'),
    (b'\x89PNG', 'image/png'),
    (b'\xff\xd8\xff', 'image/jpeg'),
    (b'\xff\x0b', 'image/jpeg'),
)

# Extension-specific MIME types for content that has no binary magic
# signature (plain text, HTML).
_TEXT_LIKE = {'txt', 'html', 'htm', 'xml', 'json', 'csv', 'log'}


def _sniff_header(content: bytes, ext: str) -> Optional[str]:
    """Return a MIME type from a header-based sniffer, or ``None``.

    The returned type is deliberately coarse: zip containers may be
    either ``.docx`` or ``.xlsx`` so we return the family MIME
    (``application/vnd.openxmlformats-officedocument``) and let the
    caller compare against the family's allowed set.
    """
    for sig, mime in _SIGNATURES:
        if content.startswith(sig):
            return mime
    ext_lower = (ext or '').lower().lstrip('.')
    if ext_lower in _TEXT_LIKE:
        return 'text/plain'
    return None


def detect_mime_type(content: bytes, ext: str) -> Tuple[Optional[str], Optional[str]]:
    """Detect a MIME type from the first 2 KB of content.

    Returns ``(mime_type, error)``.  ``mime_type`` is ``None`` when the
    content could not be identified.  ``error`` is a human-readable
    string when detection failed, otherwise ``None``.
    """
    ext_lower = (ext or '').lower().lstrip('.')
    family_mimes = {
        'docx': ('application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                 'application/vnd.openxmlformats-officedocument'),
        'xlsx': ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                 'application/vnd.openxmlformats-officedocument'),
        'pdf': ('application/pdf',),
        'png': ('image/png',),
        'jpg': ('image/jpeg',),
        'jpeg': ('image/jpeg',),
        'gif': ('image/gif',),
        'txt': ('text/plain',),
        'doc': ('application/msword',
                'application/vnd.ms-excel',
                'application/x-msword'),
        'xls': ('application/vnd.ms-excel',),
    }
    allowed_family = set(family_mimes.get(ext_lower, ()))

    # Try python-magic lazily.  On any platform where the C extension
    # or the shared library is missing we fall through to the header
    # sniffer without raising.
    detected = None
    if _MAGIC_MODULE is not None:
        try:
            detected = _MAGIC_MODULE.from_buffer(content[:2048], mime=True)
        except Exception:
            detected = None

    if detected:
        if allowed_family and detected in allowed_family:
            return detected, None
        # ``python-magic`` may return ``application/zip`` for OOXML
        # files; allow that when the extension is a known OOXML type.
        if ext_lower in ('docx', 'xlsx') and detected == 'application/zip':
            return 'application/vnd.openxmlformats-officedocument', None
        if not allowed_family:
            return detected, None
        return detected, (
            f'File content does not match its extension. Detected: {detected}.'
        )

    # Header-based fallback.
    sniffed = _sniff_header(content, ext_lower)
    if sniffed is None:
        if ext_lower in ('txt',):
            # Plain text has no magic signature; trust the extension.
            return 'text/plain', None
        return None, ('Could not determine the MIME type of this file. '
                      'If you installed the application on Linux without '
                      'libmagic1, run ``apt-get install -y libmagic1``.')

    if allowed_family and sniffed not in allowed_family:
        return sniffed, (
            f'File content does not match its extension. Detected: {sniffed}.'
        )
    return sniffed, None
