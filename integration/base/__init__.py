"""
Base module containing abstract classes and core integrations.

This module provides:
- CatalogBase: Abstract base class for all e-commerce platform adapters
- Integrations: Enum of supported integration platforms
"""

from base.base import CatalogBase
from base.integrations import Integrations

__all__ = ["CatalogBase", "Integrations"]
