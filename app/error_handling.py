"""Server-side diagnostics for unexpected route failures.

User-facing messages must never contain raw exception text.  Database
errors in particular embed the failing SQL statement and its bound
parameters, which can include password hashes, reset tokens, licence
keys and patient identifiers.  Routes therefore show a generic message
and call :func:`log_unexpected_error`, which writes the full diagnostic
detail to the server log with secret-shaped values redacted.

The traceback is formatted frame-by-frame (``traceback.format_tb``)
rather than with ``traceback.format_exc`` so the final exception line is
never emitted verbatim; the exception type and message are logged
separately after :func:`redact_text` has scrubbed them.
"""
import logging
import re
import traceback

from flask import current_app, has_app_context

_REDACTED = '<redacted>'

# ``password=...`` / ``token: ...`` style key/value pairs.  Covers the
# bound-parameter rendering SQLAlchemy includes in driver errors.
_SECRET_PAIR_RE = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key|authorization|"
    r"session|csrf|credential|license[_-]?key)\b"
    r"\s*[:=]\s*(?:'[^']*'|\"[^\"]*\"|[^\s,;)\]}]+)"
)

# Userinfo embedded in a connection URL: scheme://user:password@host.
_URL_CREDENTIALS_RE = re.compile(r"(?i)([a-z][a-z0-9+.\-]*://)[^/\s@]+@")

# Bearer tokens and JWTs.
_BEARER_RE = re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._\-]+")
_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+")


def redact_text(value):
    """Return ``value`` as a string with secret-shaped substrings masked.

    This is a defence-in-depth filter, not a guarantee.  Callers should
    still avoid passing credential-bearing structures to the logger.
    """
    if value is None:
        return ''
    text = str(value)
    text = _SECRET_PAIR_RE.sub(lambda m: f'{m.group(1)}={_REDACTED}', text)
    text = _URL_CREDENTIALS_RE.sub(lambda m: f'{m.group(1)}{_REDACTED}@', text)
    text = _BEARER_RE.sub(lambda m: f'{m.group(1)} {_REDACTED}', text)
    text = _JWT_RE.sub(_REDACTED, text)
    return text


def user_error_message(action):
    """Return the generic message shown when ``action`` fails unexpectedly.

    ``action`` is a verb phrase such as ``'create the user'``.  The
    message deliberately contains no exception detail, record values or
    identifiers; those belong in the server log (see
    :func:`log_unexpected_error`).  Callers roll the transaction back
    before flashing, so "No changes were saved" is accurate.
    """
    return (
        f'Sorry, the system could not {action} because of an unexpected '
        'server error. No changes were saved. Please try again; if the '
        'problem continues, contact an administrator.'
    )


def log_unexpected_error(operation, exc, **context):
    """Log an unexpected failure at ERROR level without leaking secrets.

    Parameters
    ----------
    operation:
        Short, human-readable description of the failed action, e.g.
        ``'create department'``.  Appears in the log line.
    exc:
        The caught exception.  Its type, redacted message and full frame
        stack are logged.
    **context:
        Optional, non-sensitive identifiers (usernames, codes, record
        ids) that help an operator correlate the log entry with the
        request.  Values are redacted before logging; never pass
        passwords, tokens, whole form payloads or credentials.
    """
    logger = (current_app.logger if has_app_context()
              else logging.getLogger(__name__))
    stack = ''.join(traceback.format_tb(exc.__traceback__))
    safe_context = {key: redact_text(val) for key, val in context.items()
                    if val is not None}
    logger.error(
        'Unhandled error during %s: %s: %s | context=%s\n%s',
        operation,
        type(exc).__name__,
        redact_text(exc),
        safe_context,
        redact_text(stack),
    )
