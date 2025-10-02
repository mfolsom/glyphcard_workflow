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
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCEPTANCE_FILE = os.path.join(BASE_DIR, "acceptance.yaml")

def load_yaml(path):
    if not os.path.exists(path):
        return {"pending_reviews": [], "accepted": [], "needs_revision": []}
    with open(path) as f:
        return yaml.safe_load(f)

def show_review_queue():
    data = load_yaml(ACCEPTANCE_FILE)
    
    print("\n📋 TASKS PENDING REVIEW")
    print("=" * 70)
    if data["pending_reviews"]:
        for task in data["pending_reviews"]:
            print(f"ID: {task['id']} - {task['title']}")
            print(f"   Assignee: {task['assignee']} | Size: {task.get('size', 'unknown')}")
            print(f"   Submitted: {task['submitted_date']}")
            
            if task.get('deliverables'):
                print("   Deliverables:")
                for deliverable in task['deliverables']:
                    print(f"     • {deliverable}")
            
            if task.get('validation'):
                print("   Validation Criteria:")
                for criteria in task['validation']:
                    print(f"     ✓ {criteria}")
            
            if task.get('output_location'):
                print(f"   Output: {task['output_location']}")
            
            print()
    else:
        print("No tasks pending review")
    
    print("\n🔁 TASKS NEEDING REVISION")
    print("=" * 50)
    if data.get("needs_revision"):
        for task in data["needs_revision"]:
            print(f"ID: {task['id']} - {task['title']}")
            print(f"   Notes: {task['notes']}")
            print(f"   Requested: {task['revision_requested']}")
            print()
    else:
        print("No tasks need revision")
    
    print("\n✅ RECENTLY ACCEPTED TASKS")
    print("=" * 50)
    if data["accepted"]:
        # Show last 5 accepted tasks
        for task in data["accepted"][-5:]:
            print(f"ID: {task['id']} - {task['title']}")
            print(f"   Accepted: {task['accepted_date']}")
            print()
    else:
        print("No accepted tasks yet")

if __name__ == "__main__":
    show_review_queue()