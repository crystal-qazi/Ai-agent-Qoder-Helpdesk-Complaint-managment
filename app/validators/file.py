"""File upload/download validators."""
import os
import magic
from flask import current_app
from app.models import Attachment


# Allowed MIME types by extension
ALLOWED_MIME_TYPES = {
    'pdf': ['application/pdf'],
    'png': ['image/png'],
    'jpg': ['image/jpeg'],
    'jpeg': ['image/jpeg'],
    'gif': ['image/gif'],
    'txt': ['text/plain'],
    'doc': ['application/msword'],
    'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    'xls': ['application/vnd.ms-excel'],
    'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
}

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_file_upload(file, allowed_extensions=None, max_size=None):
    """Validate file upload."""
    errors = {}
    
    if not file or not file.filename:
        errors['file'] = 'No file selected.'
        return errors, None
    
    # Get allowed extensions from config
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', set())
    
    # Get max size from config
    if max_size is None:
        max_size = current_app.config.get('MAX_FILE_SIZE', MAX_FILE_SIZE)
    
    # Check file extension
    filename = file.filename
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in allowed_extensions:
        errors['file'] = f'File extension ".{ext}" is not allowed. Allowed: {", ".join(sorted(allowed_extensions))}.'
        return errors, None
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > max_size:
        errors['file'] = f'File size ({file_size / 1024 / 1024:.1f} MB) exceeds maximum allowed size ({max_size / 1024 / 1024:.1f} MB).'
        return errors, None
    
    if file_size == 0:
        errors['file'] = 'File is empty.'
        return errors, None
    
    # Validate MIME type using python-magic
    try:
        file_content = file.read(2048)
        file.seek(0)
        mime_type = magic.from_buffer(file_content, mime=True)
        
        # Check if MIME type matches extension
        allowed_mimes = ALLOWED_MIME_TYPES.get(ext, [])
        if allowed_mimes and mime_type not in allowed_mimes:
            errors['file'] = f'File content does not match its extension. Detected: {mime_type}.'
            return errors, None
        
        return errors, {
            'original_filename': sanitize_filename(filename),
            'mime_type': mime_type,
            'file_size': file_size,
            'extension': ext,
        }
    except Exception as e:
        errors['file'] = f'File validation failed: {str(e)}'
        return errors, None


def validate_file_download(attachment, user):
    """Validate file download authorization."""
    from app.permissions.policy import PermissionPolicy
    
    if not PermissionPolicy.can_download_attachment(user, attachment):
        return False, 'You do not have permission to download this file.'
    
    # Check if file exists
    if not os.path.exists(attachment.storage_path):
        return False, 'File not found on server.'
    
    return True, None


def sanitize_filename(filename):
    """Sanitize filename for safe storage."""
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove special characters
    import re
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return f'{name}{ext}'


def generate_stored_filename(original_filename):
    """Generate a unique stored filename."""
    import uuid
    from datetime import datetime
    
    ext = os.path.splitext(original_filename)[1].lower()
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    unique_id = uuid.uuid4().hex[:8]
    return f'{timestamp}_{unique_id}{ext}'