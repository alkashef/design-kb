"""LanceStore: the only module that imports LanceDB (D-15, D-21)."""

import logging

import lancedb

logger = logging.getLogger(__name__)


class LanceStore:
    """Opens the LanceDB folder and reads and writes its tables."""

    def __init__(self, data_dir: str):
        """Open or create the LanceDB folder data_dir."""
        self._db = lancedb.connect(data_dir)
        logger.info("Opened the store.")
