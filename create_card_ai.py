#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-friendly card creation script for Glyphcard system
Copyright (c) 2025 Megan Folsom

This file is part of Glyphcard.

Glyphcard is free software: you can redistribute it and/or modify
it under the terms of the MIT License. See the LICENSE file in the
project root for more information.
"""

import os
import yaml
import argparse
from typing import List, Optional

from dependency_manager import is_card_accepted

def get_active_project() -> Optional[str]:
    """Get the currently active project from project manager, if any."""
    try:
        from project_manager import ProjectManager
        pm = ProjectManager()
        return pm.get_active_project()
    except Exception:
        return None

def make_card_id(existing_files: List[str]) -> str:
    """Generate the next card ID based on existing files."""
    existing_ids = [int(f.split("_")[0]) for f in existing_files if f.split("_")[0].isdigit()]
    return str(max(existing_ids + [0]) + 1).zfill(3)


def create_card(
    title: str,
    project: Optional[str] = None,
    assigned_to: str = "claude",
    size: str = "2-4 hours",
    context_needs: Optional[List[str]] = None,
    deliverables: Optional[List[str]] = None,
    validation: Optional[List[str]] = None,
    open_questions: Optional[List[str]] = None,
    linked_to: Optional[str] = None
) -> str:
    """
    Create a new Glyphcard programmatically.
    
    Args:
        title: Card title
        project: Project name (defaults to active project if in project mode)
        assigned_to: Who the card is assigned to (default: claude)
        size: Estimated time to complete (default: 2-4 hours)
        context_needs: List of context requirements
        deliverables: List of deliverables
        validation: List of validation steps
        open_questions: List of open questions
        linked_to: ID of linked card (optional)
    
    Returns:
        Path to the created card file
    """
    # Auto-detect project from active context if not specified
    if project is None:
        project = get_active_project()
        if project is None:
            raise ValueError("No project specified and no active project found. Use activate_project first or specify project explicitly.")
    
    cards_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "glyphcards"))
    os.makedirs(cards_dir, exist_ok=True)

    files = os.listdir(cards_dir)
    card_id = make_card_id(files)
    filename = f"{card_id}_{title.lower().replace(' ', '_').replace(':', '').replace('/', '_')}.yaml"
    
    linked_reference = None
    if linked_to and linked_to != "None":
        # Prefer numeric IDs when possible for dependency detection
        try:
            linked_reference = int(str(linked_to).strip())
        except ValueError:
            linked_reference = str(linked_to).strip()

    card_status = "available"
    if linked_reference is not None:
        card_status = "blocked"
        if is_card_accepted(linked_reference):
            card_status = "available"

    card = {
        "id": int(card_id),
        "title": title,
        "status": card_status,
        "assigned_to": assigned_to,
        "project": project,
        "size": size,
        "context_needs": context_needs or [],
        "deliverables": deliverables or [],
        "validation": validation or [],
        "open_questions": open_questions or [],
        "linked_to": linked_reference
    }

    filepath = os.path.join(cards_dir, filename)
    with open(filepath, "w") as f:
        yaml.dump(card, f, default_flow_style=False, sort_keys=False)

    print(f"✅ Glyphcard saved to: glyphcards/{filename}")
    return filepath


def main():
    """Command-line interface for creating cards."""
    parser = argparse.ArgumentParser(description="Create a new Glyphcard")
    parser.add_argument("title", help="Card title")
    parser.add_argument("project", help="Project name")
    parser.add_argument("--assigned-to", default="claude", help="Assignee (default: claude)")
    parser.add_argument("--size", default="2-4 hours", help="Estimated size (default: 2-4 hours)")
    parser.add_argument("--context-needs", nargs="*", help="Context needs")
    parser.add_argument("--deliverables", nargs="*", help="Deliverables")
    parser.add_argument("--validation", nargs="*", help="Validation steps")
    parser.add_argument("--open-questions", nargs="*", help="Open questions")
    parser.add_argument("--linked-to", help="Linked card ID")
    
    args = parser.parse_args()
    
    create_card(
        title=args.title,
        project=args.project,
        assigned_to=args.assigned_to,
        size=args.size,
        context_needs=args.context_needs,
        deliverables=args.deliverables,
        validation=args.validation,
        open_questions=args.open_questions,
        linked_to=args.linked_to
    )


if __name__ == "__main__":
    main()
