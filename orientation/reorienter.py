
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
import json
import argparse
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GLYPHCARDS_DIR = os.path.join(BASE_DIR, "..", "glyphcards")
STATE_FILE = os.path.join(BASE_DIR, "system_state.json")
DECISIONS_FILE = os.path.join(BASE_DIR, "decisions.log")
OUTPUT_DIR = BASE_DIR

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def load_json(path):
    with open(path) as f:
        return json.load(f)

def save_yaml(data, path):
    with open(path, "w") as f:
        yaml.dump(data, f)

def get_orientation_packet(card_id):
    # Find the glyphcard file
    card_file = next((f for f in os.listdir(GLYPHCARDS_DIR) if f.startswith(card_id)), None)
    if not card_file:
        raise FileNotFoundError(f"No glyphcard file starting with ID {card_id}")

    card = load_yaml(os.path.join(GLYPHCARDS_DIR, card_file))
    system_state = load_json(STATE_FILE)
    decisions = load_yaml(DECISIONS_FILE)

    # Determine linked modules
    linked_modules = {}
    for key, val in system_state.items():
        if card_id in val.get("linked_cards", []):
            linked_modules[key] = val

    # Relevant decisions
    relevant_decisions = [
        d for d in decisions
        if any(deliv in d["affected"] for deliv in card.get("deliverables", []))
    ]

    packet = {
        "card_id": card["id"],
        "title": card["title"],
        "assigned_to": card.get("assigned_to", "unassigned"),
        "date": datetime.datetime.now().isoformat(),
        "summary": card.get("description", "No summary provided."),
        "context_brief": {
            "context_needs": card.get("context_needs", []),
            "linked_modules": linked_modules
        },
        "recent_decisions": relevant_decisions,
        "open_questions": card.get("open_questions", []),
        "deliverables": card.get("deliverables", []),
        "validation": card.get("validation", []),
        "review_notes": card.get("review_notes", [])
    }

    out_path = os.path.join(OUTPUT_DIR, f"orientation_packet_{card['id']}.yaml")
    save_yaml(packet, out_path)
    return out_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--card", required=True, help="Glyphcard ID to generate orientation packet for")
    args = parser.parse_args()

    path = get_orientation_packet(args.card)
    print(f"Orientation packet written to {path}")
