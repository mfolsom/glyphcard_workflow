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
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import subprocess
from collections import defaultdict

app = Flask(__name__)
app.config['SECRET_KEY'] = 'glyphcard-pm-dashboard-secret'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GLYPHCARDS_DIR = os.path.join(BASE_DIR, "glyphcards")
ACCEPTANCE_FILE = os.path.join(BASE_DIR, "acceptance.yaml")
ARCHIVE_DIR = os.path.join(BASE_DIR, "archive", "glyphcards")

def load_yaml(path):
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return yaml.safe_load(f)

def save_yaml(data, path):
    with open(path, "w") as f:
        yaml.dump(data, f, sort_keys=False)

def get_card_details(card_id):
    """Get full glyphcard details from glyphcard file"""
    # Convert card_id to zero-padded string to match filename format
    card_id_str = str(card_id).zfill(3)
    card_file = next((f for f in os.listdir(GLYPHCARDS_DIR) if f.startswith(card_id_str)), None)
    if not card_file:
        return None
    card_path = os.path.join(GLYPHCARDS_DIR, card_file)
    return load_yaml(card_path)

def get_output_content(card_id, assignee):
    """Try to get the output content for a glyphcard"""
    # Convert card_id to zero-padded string to match filename format
    card_id_str = str(card_id).zfill(3)
    output_paths = [
        f"agent_workspaces/{assignee.lower()}/card_{card_id_str}_demo_output.md",
        f"agents/{assignee.lower()}/card_{card_id_str}_demo_output.md",  # Legacy path
        f"agent_workspaces/{assignee.lower()}/task_{card_id_str}_output.md",
        f"agents/{assignee.lower()}/task_{card_id_str}_output.md",  # Legacy path
        f"agent_workspaces/{assignee.lower()}/output_{card_id_str}.md",
        f"agent_workspaces/{assignee.lower()}/output.md"
    ]
    for path in output_paths:
        full_path = os.path.join(BASE_DIR, path)
        if os.path.exists(full_path):
            with open(full_path, 'r') as f:
                return f.read()
    return None


def _normalize_card_id(value):
    """Return zero-padded string representation of a glyphcard ID."""
    if value in (None, "None", ""):
        return None
    try:
        return str(int(value)).zfill(3)
    except (TypeError, ValueError):
        value_str = str(value).strip()
        if value_str.isdigit():
            return value_str.zfill(3)
        return value_str or None


def _load_all_glyphcards():
    """Load all glyphcard files into memory for dependency visualization."""
    cards = []
    if not os.path.exists(GLYPHCARDS_DIR):
        return cards
    for filename in sorted(os.listdir(GLYPHCARDS_DIR)):
        if not filename.endswith(".yaml"):
            continue
        card_path = os.path.join(GLYPHCARDS_DIR, filename)
        card = load_yaml(card_path)
        if not card:
            continue
        try:
            card_id = int(card.get("id", filename.split("_")[0]))
        except (TypeError, ValueError):
            continue
        card["id"] = card_id
        card["_id_str"] = _normalize_card_id(card_id)
        card["_linked_to_str"] = _normalize_card_id(card.get("linked_to"))
        cards.append(card)
    return cards


def _build_dependency_view():
    """Construct dependency trees and metadata for UI rendering."""
    cards = _load_all_glyphcards()
    by_id = {card["_id_str"]: card for card in cards if card.get("_id_str")}
    children = defaultdict(list)
    missing_links = []

    for card in cards:
        parent_id = card.get("_linked_to_str")
        card_id = card.get("_id_str")
        if not card_id:
            continue
        if parent_id and parent_id in by_id:
            children[parent_id].append(card_id)
        elif parent_id and parent_id not in by_id:
            missing_links.append({
                "card": card,
                "missing_id": parent_id
            })

    roots = [cid for cid, card in by_id.items()
             if not card.get("_linked_to_str") or card.get("_linked_to_str") not in by_id]
    roots = sorted(set(roots))

    def build_node(current_id, ancestors):
        card = by_id[current_id]
        node = {
            "card": card,
            "card_id": current_id,
            "children": [],
            "cycle": current_id in ancestors
        }
        if node["cycle"]:
            return node
        new_ancestors = set(ancestors)
        new_ancestors.add(current_id)
        for child_id in sorted(children.get(current_id, [])):
            node["children"].append(build_node(child_id, new_ancestors))
        return node

    def collect_ids(node):
        collected = {node["card_id"]}
        for child in node.get("children", []):
            collected.update(collect_ids(child))
        return collected

    dependency_trees = []
    visited = set()
    for root_id in roots:
        node = build_node(root_id, set())
        dependency_trees.append(node)
        visited.update(collect_ids(node))

    # Include any remaining cards (e.g., pure cycles) as standalone trees
    remaining_ids = sorted(set(by_id.keys()) - visited)
    for card_id in remaining_ids:
        node = build_node(card_id, set())
        dependency_trees.append(node)
        visited.update(collect_ids(node))

    unattached_cards = [by_id[cid] for cid in sorted(by_id.keys()) if cid not in visited]

    return dependency_trees, missing_links, unattached_cards

@app.route('/')
def dashboard():
    """Main dashboard view"""
    acceptance_data = load_yaml(ACCEPTANCE_FILE)
    # Enhance pending reviews with glyphcard details
    for card in acceptance_data.get('pending_reviews', []):
        card_details = get_card_details(card['id'])
        if card_details:
            card['status'] = card_details.get('status', 'unknown')
            card['size'] = card_details.get('size', 'Unknown')
            card['deliverables'] = card_details.get('deliverables', [])
            card['validation'] = card_details.get('validation', [])
            card['output_content'] = get_output_content(card['id'], card.get('assignee', 'unknown'))
            # Include the output_location for direct file access
            card['output_location'] = card.get('output_location', f"agent_workspaces/{card.get('assignee', 'unknown')}/output_{str(card['id']).zfill(3)}.md")
    # Filter accepted glyphcards to only show those that still exist (not archived)
    accepted_cards = []
    for card in acceptance_data.get('accepted', [])[-10:]:  # Last 10
        if get_card_details(card['id']):  # Card still exists in glyphcards dir
            accepted_cards.append(card)
    return render_template('dashboard.html',
                           view='cards',
                           pending=acceptance_data.get('pending_reviews', []),
                           needs_revision=acceptance_data.get('needs_revision', []),
                           accepted=accepted_cards,
                           dependency_trees=[],
                           missing_links=[],
                           unattached_cards=[])

@app.route('/view_output/<card_id>')
def view_output(card_id):
    """Serve the agent output file for review"""
    acceptance_data = load_yaml(ACCEPTANCE_FILE)
    
    # Find the card in pending reviews
    card_info = None
    for card in acceptance_data.get('pending_reviews', []):
        if str(card['id']) == str(card_id):
            card_info = card
            break
    
    if not card_info:
        return "Output file not found - card not in review queue", 404
    
    output_location = card_info.get('output_location')
    if not output_location:
        return "No output location specified for this card", 404
    
    output_path = os.path.join(BASE_DIR, output_location)
    if not os.path.exists(output_path):
        return f"Output file not found at: {output_location}", 404
    
    with open(output_path, 'r') as f:
        content = f.read()
    
    # Return as plain text with proper formatting
    from flask import Response
    return Response(content, mimetype='text/plain')

@app.route('/review/<card_id>', methods=['POST'])
def review_card(card_id):
    """Handle glyphcard review submission"""
    action = request.form.get('action')
    notes = request.form.get('notes', '')
    if action == 'accept':
        cmd = ['python', 'review_card.py', card_id, 'accept']
    elif action == 'changes_needed':
        cmd = ['python', 'review_card.py', card_id, 'changes_needed', '--notes', notes]
    else:
        return jsonify({'error': 'Invalid action'}), 400
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=BASE_DIR)
        if result.returncode == 0:
            return redirect(url_for('dashboard'))
        else:
            return jsonify({'error': result.stderr}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/dependencies')
def dependency_dashboard():
    """Render dependency chain view for PMs."""
    dependency_trees, missing_links, unattached_cards = _build_dependency_view()
    return render_template('dashboard.html',
                           view='dependencies',
                           pending=[],
                           needs_revision=[],
                           accepted=[],
                           dependency_trees=dependency_trees,
                           missing_links=missing_links,
                           unattached_cards=unattached_cards)

@app.route('/archive/<card_id>', methods=['POST'])
def archive_card(card_id):
    """Archive a completed glyphcard"""
    try:
        card_file = next((f for f in os.listdir(GLYPHCARDS_DIR) if f.startswith(card_id)), None)
        if not card_file:
            # Check if already archived
            if os.path.exists(ARCHIVE_DIR):
                archived_file = next((f for f in os.listdir(ARCHIVE_DIR) if f.startswith(card_id)), None)
                if archived_file:
                    return jsonify({'error': 'Glyphcard already archived'}), 400
            return jsonify({'error': 'Glyphcard not found'}), 404
        # Create archive directory if needed
        os.makedirs(ARCHIVE_DIR, exist_ok=True)
        # Move glyphcard file to archive
        src = os.path.join(GLYPHCARDS_DIR, card_file)
        dst = os.path.join(ARCHIVE_DIR, card_file)
        os.rename(src, dst)
        # Update system_state.json
        system_state_file = os.path.join(BASE_DIR, "orientation", "system_state.json")
        if os.path.exists(system_state_file):
            with open(system_state_file) as f:
                system_state = json.load(f)
            # Find and update the module linked to this glyphcard
            for module_name, module_data in system_state.items():
                if "linked_cards" in module_data and card_id in module_data["linked_cards"]:
                    module_data["status"] = "archived"
                    module_data["archived_date"] = datetime.now().isoformat()
                    break
            with open(system_state_file, "w") as f:
                json.dump(system_state, f, indent=2)
        return redirect(url_for('dashboard'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
