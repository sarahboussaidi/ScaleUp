"""
bmc/__init__.py
Exposes the top-level pipeline entry point.
"""

from bmc_eval_scripts.pipeline import run

__all__ = ["run"]