"""
Collection Registry — Persists collection names even when empty.
Uses a simple JSON file for storage.
"""
from __future__ import annotations
import json
from pathlib import Path
from config import settings

class CollectionRegistry:
    def __init__(self, path: str):
        self.path = Path(path)
        self._collections: set[str] = set()
        self._load()
        # If still empty after load, add default for first-time use
        if not self._collections:
            self._collections.add("default")
            self._save()

    def _load(self) -> None:
        """Load collections from JSON file."""
        if not self.path.exists():
            return
        
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._collections.update(data)
        except Exception as e:
            print(f"[Registry] Error loading {self.path}: {e}")

    def _save(self) -> None:
        """Save unique collections to JSON file."""
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(sorted(list(self._collections)), f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[Registry] Error saving {self.path}: {e}")

    def add(self, name: str) -> None:
        """Add a collection name and persist."""
        name = name.strip().lower()
        if not name:
            return
        self._collections.add(name)
        self._save()

    def remove(self, name: str) -> None:
        """Remove a collection name and persist."""
        if name in self._collections:
            self._collections.remove(name)
            self._save()

    def get_all(self) -> list[str]:
        """Return all registered collection names."""
        return sorted(list(self._collections))

collection_registry = CollectionRegistry(settings.collections_registry_path)
