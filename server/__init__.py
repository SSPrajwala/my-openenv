# server package — exposes the FastAPI app at the package level
from server.app import app

__all__ = ["app"]
