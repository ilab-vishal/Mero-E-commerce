"""
Enum of supported e-commerce platform integrations.

Add new platforms here when extending the system.
"""

from enum import Enum


class Integrations(Enum):
    """
    Supported e-commerce platform integrations.

    Each value represents a platform identifier used in the factory
    pattern to instantiate the correct engine.
    """

    SHOPIFY: str = "shopify"
