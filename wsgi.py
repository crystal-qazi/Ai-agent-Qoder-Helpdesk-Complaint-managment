#!/usr/bin/env python
"""Production WSGI entry point."""
import os
from app import create_app

app = create_app(os.environ.get('FLASK_ENV', 'production'))

if __name__ == '__main__':
    app.run()