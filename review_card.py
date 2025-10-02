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

from dependency_manager import reconcile_block_statuses

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARDS_DIR = os.path.join(BASE_DIR, "glyphcards")
ACCEPTANCE_FILE = os.path.join(BASE_DIR, "acceptance.yaml")
SYSTEM_STATE_FILE = os.path.join(BASE_DIR, "orientation", "system_state.json")

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def save_yaml(data, path):
    with open(path, "w") as f:
        yaml.dump(data, f, sort_keys=False)

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)

def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def find_card_file(card_id):
    card_file = next((f for f in os.listdir(CARDS_DIR) if f.startswith(card_id)), None)
    if not card_file:
        raise FileNotFoundError(f"No glyphcard file starting with ID {card_id}")
    return os.path.join(CARDS_DIR, card_file)

def load_acceptance_data():
    if not os.path.exists(ACCEPTANCE_FILE):
        return {"pending_reviews": [], "accepted": [], "needs_revision": []}
    return load_yaml(ACCEPTANCE_FILE)

def save_acceptance_data(data):
    save_yaml(data, ACCEPTANCE_FILE)

def update_card_status(card_path, status, review_notes=None):
    card = load_yaml(card_path)
    card["status"] = status
    card["reviewed_at"] = datetime.datetime.now().isoformat()
    
    if review_notes:
        if "review_notes" not in card:
            card["review_notes"] = []
        card["review_notes"].append({
            "date": datetime.datetime.now().isoformat(),
            "notes": review_notes
        })
    
    save_yaml(card, card_path)
    return card

def accept_card(card_id, reviewer="human"):
    card_path = find_card_file(card_id)
    card = update_card_status(card_path, "accepted")
    
    # Update acceptance.yaml
    acceptance_data = load_acceptance_data()
    
    # Remove from pending if present
    acceptance_data["pending_reviews"] = [
        c for c in acceptance_data["pending_reviews"] if c["id"] != card_id
    ]
    
    # Remove from needs_revision if present (acceptance takes precedence)
    if "needs_revision" in acceptance_data:
        acceptance_data["needs_revision"] = [
            c for c in acceptance_data["needs_revision"] if c["id"] != card_id
        ]
    
    # Add to accepted
    acceptance_data["accepted"].append({
        "id": card_id,
        "title": card.get("title", ""),
        "accepted_date": datetime.datetime.now().isoformat(),
        "reviewer": reviewer,
        "notes": "Glyphcard accepted and validated"
    })
    
    save_acceptance_data(acceptance_data)
    
    # Update system_state.json
    system_state = load_json(SYSTEM_STATE_FILE)
    
    # Find the module linked to this card
    for module_data in system_state.values():
        if card_id in module_data.get("linked_cards", []):
            module_data["status"] = "accepted"
            module_data["accepted_date"] = datetime.datetime.now().isoformat()
            break
    
    save_json(system_state, SYSTEM_STATE_FILE)

    # Reconcile downstream card statuses now that dependencies may be satisfied
    reconcile_block_statuses()
    print(f"✅ Glyphcard {card_id} accepted!")

def request_changes(card_id, notes, reviewer="human"):
    card_path = find_card_file(card_id)
    card = update_card_status(card_path, "needs_revision", notes)
    
    # Update acceptance.yaml
    acceptance_data = load_acceptance_data()
    
    # Remove from pending if present
    acceptance_data["pending_reviews"] = [
        c for c in acceptance_data["pending_reviews"] if c["id"] != card_id
    ]
    
    # Add to needs_revision
    if "needs_revision" not in acceptance_data:
        acceptance_data["needs_revision"] = []
        
    acceptance_data["needs_revision"].append({
        "id": card_id,
        "title": card.get("title", ""),
        "revision_requested": datetime.datetime.now().isoformat(),
        "reviewer": reviewer,
        "notes": notes
    })
    
    save_acceptance_data(acceptance_data)
    
    # Re-block dependent cards if necessary
    reconcile_block_statuses()
    print(f"🔁 Glyphcard {card_id} needs revision. Notes added to card.")

def add_to_review_queue(card_id):
    """Called by submit_output.py to add glyphcard to review queue"""
    card_path = find_card_file(card_id)
    card = load_yaml(card_path)
    
    acceptance_data = load_acceptance_data()
    
    # Check if already in pending
    if any(c["id"] == card_id for c in acceptance_data["pending_reviews"]):
        return
    
    # Remove from needs_revision if present (resubmission)
    if "needs_revision" in acceptance_data:
        acceptance_data["needs_revision"] = [
            c for c in acceptance_data["needs_revision"] if c["id"] != card_id
        ]
    
    # Gather orientation packet info if available
    orientation_packet_path = os.path.join(
        BASE_DIR, "orientation", f"orientation_packet_{card_id}.yaml"
    )
    orientation_info = {}
    if os.path.exists(orientation_packet_path):
        orientation_data = load_yaml(orientation_packet_path)
        orientation_info = {
            "summary": orientation_data.get("summary", "No summary provided"),
            "deliverables": orientation_data.get("deliverables", []),
            "validation": orientation_data.get("validation", [])
        }
    
    acceptance_data["pending_reviews"].append({
        "id": card_id,
        "title": card.get("title", ""),
        "submitted_date": datetime.datetime.now().isoformat(),
        "assignee": card.get("assigned_to", "unknown"),
        "size": card.get("size", "unknown"),
        "deliverables": card.get("deliverables", []),
        "validation": card.get("validation", []),
        "orientation_info": orientation_info,
        "output_location": f"agent_workspaces/{card.get('assigned_to', 'unknown').lower()}/output_{card_id}.md"
    })
    
    save_acceptance_data(acceptance_data)
    print(f"📋 Glyphcard {card_id} added to review queue with full context")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Review and accept/reject completed glyphcards")
    parser.add_argument("card_id", help="Glyphcard ID to review (e.g., 001)")
    parser.add_argument("action", choices=["accept", "changes_needed"], 
                       help="Action to take on the glyphcard")
    parser.add_argument("--notes", "-n", help="Review notes (required for changes_needed)")
    parser.add_argument("--reviewer", default="human", help="Name of reviewer")
    
    args = parser.parse_args()
    
    if args.action == "accept":
        accept_card(args.card_id, args.reviewer)
    elif args.action == "changes_needed":
        if not args.notes:
            parser.error("--notes required when requesting changes")
        request_changes(args.card_id, args.notes, args.reviewer)
