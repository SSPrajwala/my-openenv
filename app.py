# app.py — HuggingFace Spaces entry point
# Imports the FastAPI app from server.app (multi-mode deployment pattern)
from server.app import app  # noqa: F401

__all__ = ["app"]
