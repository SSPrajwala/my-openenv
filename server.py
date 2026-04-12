"""
server.py — backward-compatibility shim
========================================
The FastAPI app now lives at server/app.py.
This file exists only for backward compatibility.
"""

from server.app import app  # noqa: F401

__all__ = ["app"]
