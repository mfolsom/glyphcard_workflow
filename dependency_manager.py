#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilities for enforcing glyphcard dependency rules."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

BASE_DIR = Path(__file__).parent
GLYPHCARDS_DIR = BASE_DIR / "glyphcards"
ACCEPTANCE_FILE = BASE_DIR / "acceptance.yaml"

CardId = Union[int, str]


def _parse_card_id(value: Any) -> Optional[CardId]:
    """Normalize a glyphcard identifier to int when numeric, else trimmed string."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "null" or text.lower() == "none":
        return None
    return int(text) if text.isdigit() else text


def _format_card_id(value: CardId) -> str:
    if isinstance(value, int):
        return f"{value:03d}"
    return str(value)


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open() as fh:
        data = yaml.safe_load(fh) or {}
    return data


def _save_yaml(data: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        yaml.dump(data, fh, sort_keys=False)


def load_all_cards() -> List[Dict[str, Any]]:
    """Load all glyphcard YAML files with metadata for dependency analysis."""
    cards: List[Dict[str, Any]] = []
    if not GLYPHCARDS_DIR.exists():
        return cards
    for filename in sorted(os.listdir(GLYPHCARDS_DIR)):
        if not filename.endswith(".yaml"):
            continue
        path = GLYPHCARDS_DIR / filename
        data = _load_yaml(path)
        if not data:
            continue
        card_id = _parse_card_id(data.get("id"))
        cards.append({
            "path": path,
            "data": data,
            "id": card_id,
            "id_str": _format_card_id(card_id) if card_id is not None else path.stem,
        })
    return cards


def _collect_acceptance_state(acceptance_data: Optional[Dict[str, Any]] = None) -> Tuple[set, set, set, set]:
    acceptance = acceptance_data or _load_yaml(ACCEPTANCE_FILE)
    accepted_ints, accepted_strs = set(), set()
    pending_ints, pending_strs = set(), set()

    for record in acceptance.get("accepted", []):
        parsed = _parse_card_id(record.get("id"))
        if isinstance(parsed, int):
            accepted_ints.add(parsed)
        elif parsed is not None:
            accepted_strs.add(parsed)

    for record in acceptance.get("pending_reviews", []):
        parsed = _parse_card_id(record.get("id"))
        if isinstance(parsed, int):
            pending_ints.add(parsed)
        elif parsed is not None:
            pending_strs.add(parsed)

    return accepted_ints, accepted_strs, pending_ints, pending_strs


def _iter_linked_ids(raw_value: Any) -> List[CardId]:
    if raw_value in (None, "", "None", "null"):
        return []
    if isinstance(raw_value, (list, tuple, set)):
        values = raw_value
    else:
        values = [raw_value]
    parsed: List[CardId] = []
    for item in values:
        parsed_id = _parse_card_id(item)
        if parsed_id is not None:
            parsed.append(parsed_id)
    return parsed


def compute_dependency_state(
    acceptance_data: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[CardId, Dict[str, Any]], List[Dict[str, Any]]]:
    """Return per-card dependency metadata.

    Each state entry includes:
        blocked (bool): True when any dependency is not accepted.
        missing (list): Parents that are referenced but missing.
        parents (list): Normalized parent IDs.
        pending_parents (list): Parents currently in pending review.
    """
    cards = load_all_cards()
    accepted_ints, accepted_strs, pending_ints, pending_strs = _collect_acceptance_state(acceptance_data)

    index: Dict[CardId, Dict[str, Any]] = {}
    for card in cards:
        key = card["id"] if card["id"] is not None else card["id_str"]
        index[key] = card

    state: Dict[CardId, Dict[str, Any]] = {}
    for card in cards:
        card_id = card["id"] if card["id"] is not None else card["id_str"]
        parents = _iter_linked_ids(card["data"].get("linked_to"))
        missing: List[str] = []
        pending: List[str] = []
        blocked = False

        for parent in parents:
            parent_exists = parent in index
            parent_accepted = False
            parent_pending = False

            if isinstance(parent, int):
                parent_accepted = parent in accepted_ints
                parent_pending = parent in pending_ints
            else:
                parent_accepted = parent in accepted_strs
                parent_pending = parent in pending_strs

            if not parent_exists:
                missing.append(_format_card_id(parent))
                blocked = True
            elif not parent_accepted:
                blocked = True
                if parent_pending:
                    pending.append(_format_card_id(parent))

        state[card_id] = {
            "blocked": blocked,
            "parents": [_format_card_id(pid) for pid in parents],
            "missing_parents": missing,
            "pending_parents": pending,
        }

    return state, cards


PROTECTED_STATUSES = {"accepted", "needs_revision"}


def reconcile_block_statuses(acceptance_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Update glyphcard status fields to reflect dependency blocks."""
    state, cards = compute_dependency_state(acceptance_data)
    changes: List[Dict[str, Any]] = []

    for card in cards:
        card_id = card["id"] if card["id"] is not None else card["id_str"]
        current = card["data"].get("status", "available")
        blocked = state[card_id]["blocked"]
        new_status = current

        if blocked:
            if current not in PROTECTED_STATUSES and current != "blocked":
                new_status = "blocked"
        else:
            if current == "blocked":
                new_status = "available"

        if new_status != current:
            card["data"]["status"] = new_status
            _save_yaml(card["data"], card["path"])
            changes.append({
                "id": card["data"].get("id", card["id_str"]),
                "from": current,
                "to": new_status,
            })

    return {"changes": changes, "state": state}


def is_card_blocked(card_id: CardId, acceptance_data: Optional[Dict[str, Any]] = None) -> bool:
    """Convenience helper to check if a specific card is currently blocked."""
    state, _ = compute_dependency_state(acceptance_data)
    key = card_id
    if key not in state:  # try alternate key
        key = _format_card_id(card_id)
    return state.get(key, {}).get("blocked", False)


def is_card_accepted(card_id: CardId, acceptance_data: Optional[Dict[str, Any]] = None) -> bool:
    """Return True if the given card_id is currently accepted."""
    accepted_ints, accepted_strs, _, _ = _collect_acceptance_state(acceptance_data)
    if isinstance(card_id, int):
        return card_id in accepted_ints
    return str(card_id).strip() in {str(item) for item in accepted_strs}


__all__ = [
    "compute_dependency_state",
    "reconcile_block_statuses",
    "is_card_blocked",
    "is_card_accepted",
    "load_all_cards",
]
