#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 Megan Folsom

This file is part of Glyphcard.

Glyphcard is free software: you can redistribute it and/or modify
it under the terms of the MIT License. See the LICENSE file in the
project root for more information.
"""

import os
import yaml
import argparse
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GLYPHCARDS_DIR = os.path.join(BASE_DIR, "..", "glyphcards")
STATE_FILE = os.path.join(BASE_DIR, "system_state.json")

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def save_yaml(data, path):
    with open(path, "w") as f:
        yaml.dump(data, f)

def load_json(path):
    import json
    with open(path) as f:
        return json.load(f)

def save_json(data, path):
    import json
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def mark_card_complete(card_id):
    card_file = next((f for f in os.listdir(GLYPHCARDS_DIR) if f.startswith(card_id)), None)
    if not card_file:
        raise FileNotFoundError(f"No glyphcard file starting with ID {card_id}")

    card_path = os.path.join(GLYPHCARDS_DIR, card_file)
    card = load_yaml(card_path)
    card["status"] = "awaiting_acceptance"
    card["submitted_at"] = datetime.datetime.now().isoformat()
    save_yaml(card, card_path)
    print(f"📝 Glyphcard {card_id} submitted and awaiting acceptance.")

    # Add to review queue
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from review_card import add_to_review_queue
    add_to_review_queue(card_id)


def update_system_state(card_id, module_name, updates):
    system_state = load_json(STATE_FILE)

    if module_name not in system_state:
        system_state[module_name] = {}

    system_state[module_name].update(updates)
    if "linked_cards" not in system_state[module_name]:
        system_state[module_name]["linked_cards"] = []
    if card_id not in system_state[module_name]["linked_cards"]:
        system_state[module_name]["linked_cards"].append(card_id)

    save_json(system_state, STATE_FILE)
    print(f"📘 System state updated for module: {module_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--card", required=True, help="Glyphcard ID to submit output for")
    parser.add_argument("--module", required=True, help="Module name to update in system_state")
    parser.add_argument("--status", default="completed", help="Status to set (default: completed)")
    args = parser.parse_args()

    mark_card_complete(args.card)
    update_system_state(args.card, args.module, {
        "status": args.status,
        "last_updated": datetime.datetime.now().isoformat()
    })
