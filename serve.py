#!/usr/bin/env python
"""Production server entry point using Waitress."""
import os
from dotenv import load_dotenv

load_dotenv()

from waitress import serve
from app import create_app

app = create_app(os.environ.get('FLASK_ENV', 'production'))

if __name__ == '__main__':
    host = os.environ.get('WEB_HOST', '0.0.0.0')
    port = int(os.environ.get('WEB_PORT', '5000'))
    threads = int(os.environ.get('WEB_THREADS', '8'))
    print(f"Starting Waitress on http://{host}:{port}")
    serve(app, host=host, port=port, threads=threads)
