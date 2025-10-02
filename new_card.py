
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

from dependency_manager import is_card_accepted

def prompt(question, default=None):
    response = input(f"{question} " + (f"[{default}] " if default else ""))
    return response.strip() if response.strip() else default


def make_card_id(existing_files):
    existing_ids = [int(f.split("_")[0]) for f in existing_files if f.split("_")[0].isdigit()]
    return str(max(existing_ids + [0]) + 1).zfill(3)


def generate_card():
    cards_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "glyphcards"))
    os.makedirs(cards_dir, exist_ok=True)

    files = os.listdir(cards_dir)
    id = make_card_id(files)
    title = prompt("Glyphcard title?") or "untitled"
    filename = f"{id}_{title.lower().replace(' ', '_')}.yaml"
    assigned_to = prompt("Assigned to?", "unassigned")
    project = prompt("project_name (corresponds to repo directory name)?")
    size = prompt("Estimated time to complete?", "2–4 hours")
    context_needs = prompt("Context needs (comma-separated)?", "").split(",")
    deliverables = prompt("Deliverables (comma-separated)?", "").split(",")
    validation = prompt("Validation steps (comma-separated)?", "").split(",")
    open_questions = prompt("Open questions (comma-separated)?", "").split(",")
    linked_to_raw = prompt("Linked to glyphcard ID?", "None")
    linked_reference = None
    if linked_to_raw and linked_to_raw not in ("None", "none", ""):
        cleaned = linked_to_raw.strip()
        if cleaned.isdigit():
            linked_reference = int(cleaned)
        else:
            linked_reference = cleaned
    status = "available"
    if linked_reference is not None:
        status = "blocked"
        if is_card_accepted(linked_reference):
            status = "available"

    card = {
        "id": int(id),
        "title": title,
        "status": status,
        "assigned_to": assigned_to,
        "project": project,
        "size": size,
        "context_needs": [s.strip() for s in context_needs if s.strip()],
        "deliverables": [s.strip() for s in deliverables if s.strip()],
        "validation": [s.strip() for s in validation if s.strip()],
        "open_questions": [s.strip() for s in open_questions if s.strip()],
        "linked_to": linked_reference
    }

    with open(os.path.join(cards_dir, filename), "w") as f:
        yaml.dump(card, f)

    print(f"✅ Glyphcard saved to: glyphcards/{filename}")

if __name__ == "__main__":
    generate_card()
