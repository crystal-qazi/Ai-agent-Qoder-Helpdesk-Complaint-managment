"""File upload/download validators."""
import os
import re
import uuid
from datetime import datetime
from flask import current_app
from app.models import Attachment
from app.services.mime_detection import detect_mime_type


# Allowed MIME types by extension.  OOXML families accept both the
# family MIME (returned by the header sniffer when libmagic is absent)
# and the fully-qualified MIME (returned by python-magic).
ALLOWED_MIME_TYPES = {
    'pdf': ['application/pdf'],
    'png': ['image/png'],
    'jpg': ['image/jpeg'],
    'jpeg': ['image/jpeg'],
    'gif': ['image/gif'],
    'txt': ['text/plain'],
    'doc': ['application/msword', 'application/x-msword'],
    'docx': [
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument',
    ],
    'xls': ['application/vnd.ms-excel', 'application/x-msexcel'],
    'xlsx': [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.openxmlformats-officedocument',
    ],
}

# Maximum file size (10MB by default; overridden by config).
DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024

# Filenames containing ".." anywhere are rejected — no legitimate file
# ever needs a path traversal sequence, and any that do is hostile input.
_TRAVERSAL_RE = re.compile(r'\.\.')


def validate_file_upload(file, allowed_extensions=None, max_size=None):
    """Validate a file upload.

    The validator enforces:

      * Extension is in the allow-list (config-driven).
      * File is non-empty and does not exceed the size cap.
      * MIME type from the first 2 KB matches the extension.
      * The original filename is not a path-traversal payload.

    Returns ``(errors, file_info)``.  ``errors`` is a dict with the
    field-name key and the human-readable message; ``file_info`` is
    ``None`` on failure.
    """
    errors = {}

    if not file or not file.filename:
        errors['file'] = 'No file selected.'
        return errors, None

    # Normalization step: reject any filename that contains a path
    # traversal sequence before we even look at the extension.
    if '..' in file.filename:
        errors['file'] = 'Filenames must not contain path-traversal sequences.'
        return errors, None

    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', set())
    if max_size is None:
        max_size = current_app.config.get('MAX_FILE_SIZE', DEFAULT_MAX_FILE_SIZE)

    filename = os.path.basename(file.filename)  # strip any directory part
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in allowed_extensions:
        errors['file'] = (f'File extension ".{ext}" is not allowed. '
                          f'Allowed: {", ".join(sorted(allowed_extensions))}.')
        return errors, None

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > max_size:
        errors['file'] = (f'File size ({file_size / 1024 / 1024:.1f} MB) '
                          f'exceeds maximum allowed size '
                          f'({max_size / 1024 / 1024:.1f} MB).')
        return errors, None

    if file_size == 0:
        errors['file'] = 'File is empty.'
        return errors, None

    # Sniff the MIME type from the first 2 KB.  python-magic requires
    # the system libmagic on Linux; on Windows/macOS the wheel ships
    # the library.  When libmagic is unavailable we fall back to a
    # header-based sniffer so the upload path still enforces a
    # content/extension consistency check.
    file_content = file.read(2048)
    file.seek(0)
    mime_type, sniff_error = detect_mime_type(file_content, ext)
    if sniff_error:
        errors['file'] = sniff_error
        return errors, None

    allowed_mimes = ALLOWED_MIME_TYPES.get(ext, [])
    if allowed_mimes and mime_type not in allowed_mimes:
        errors['file'] = (f'File content does not match its extension. '
                          f'Detected: {mime_type}.')
        return errors, None

    return errors, {
        'original_filename': sanitize_filename(filename),
        'mime_type': mime_type,
        'file_size': file_size,
        'extension': ext,
    }


def validate_file_download(attachment, user):
    """Validate file download authorization."""
    from app.permissions.policy import PermissionPolicy

    if not PermissionPolicy.can_download_attachment(user, attachment):
        return False, 'You do not have permission to download this file.'

    if not os.path.exists(attachment.storage_path):
        return False, 'File not found on server.'

    # Refuse to serve any path that escapes the configured upload root.
    root = os.path.abspath(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
    target = os.path.abspath(attachment.storage_path)
    if os.path.commonpath([root, target]) != root:
        return False, 'Invalid storage path.'

    return True, None


def sanitize_filename(filename):
    """Sanitize a user-supplied filename.

    Strips the directory component, any path-traversal sequences, and
    characters outside a small allow-list.  The result is at most 100
    stem characters + 8 extension characters.
    """
    filename = os.path.basename(filename)
    # Strip any path-traversal payload
    filename = _TRAVERSAL_RE.sub('.', filename)
    filename = re.sub(r'[\x00-\x1f/\\<>:"|?*]', '', filename)
    filename = re.sub(r'\s+', ' ', filename).strip()
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    if len(ext) > 8:
        ext = ext[:8]
    return f'{name}{ext}'


def generate_stored_filename(original_filename):
    """Generate a unique, collision-resistant stored filename.

    Format: ``YYYYMMDDHHMMSS_<uuid8><ext>``.  The UUID fragment makes
    it safe to write two uploads in the same second to the same complaint
    without clobbering the other.  The extension is taken from
    ``original_filename`` and lower-cased; the stem is never reused
    across complaints.
    """
    ext = os.path.splitext(original_filename)[1].lower()
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    unique_id = uuid.uuid4().hex[:12]
    return f'{timestamp}_{unique_id}{ext}'


# Typo-safe alias so older call sites that imported the constant under
# its historical name keep working.
MAX_FILE_SIZE = DEFAULT_MAX_FILE_SIZE
