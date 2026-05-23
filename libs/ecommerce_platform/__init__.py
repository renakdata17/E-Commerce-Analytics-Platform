"""
Domain core for Acme Outfitters — shared across API, workers, and producers.

The package is intentionally free of FastAPI imports so Celery stays lightweight.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
