#!/usr/bin/env python
"""Production WSGI entry point."""
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["FLASK_ENV"] = "production"

from app import create_app

app = create_app("production")
