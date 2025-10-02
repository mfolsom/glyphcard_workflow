#!/usr/bin/env python3
"""
Project Activation and Namespace Management System
Provides human-controlled project switching and context management for Glyphcard workflows.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

class ProjectManager:
    """Manages project activation, deactivation, and namespace context for Glyphcard workflows."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).parent
        self.config_dir = self.base_dir / ".glyphcard"
        self.project_state_file = self.config_dir / "project_state.json"
        self.glyphcards_dir = self.base_dir / "glyphcards"
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize project state if it doesn't exist
        self._ensure_project_state()
    
    def _ensure_project_state(self):
        """Initialize project state file if it doesn't exist."""
        if not self.project_state_file.exists():
            initial_state = {
                "active_project": None,
                "projects": {},
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
            self._save_project_state(initial_state)
    
    def _load_project_state(self) -> Dict[str, Any]:
        """Load the current project state."""
        try:
            with open(self.project_state_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._ensure_project_state()
            with open(self.project_state_file, 'r') as f:
                return json.load(f)
    
    def _save_project_state(self, state: Dict[str, Any]):
        """Save project state to disk."""
        state["last_updated"] = datetime.now().isoformat()
        with open(self.project_state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def discover_projects(self) -> List[str]:
        """Discover all projects by scanning glyphcard project fields and managed projects."""
        projects = set()
        
        # First, scan existing cards for projects
        if self.glyphcards_dir.exists():
            for card_file in self.glyphcards_dir.glob("*.yaml"):
                try:
                    with open(card_file, 'r') as f:
                        card_data = yaml.safe_load(f)
                        project = card_data.get("project")
                        if project and isinstance(project, str):
                            projects.add(project)
                except (yaml.YAMLError, OSError):
                    continue
        
        # Also include projects created via create_project (even with no cards yet)
        state = self._load_project_state()
        managed_projects = state.get("projects", {})
        for project_name in managed_projects.keys():
            projects.add(project_name)
        
        return sorted(list(projects))
    
    def list_projects(self) -> Dict[str, Any]:
        """List all available projects with status information."""
        state = self._load_project_state()
        discovered_projects = self.discover_projects()
        active_project = state.get("active_project")
        
        project_info = []
        for project in discovered_projects:
            # Count cards in this project
            card_count = self._count_cards_in_project(project)
            
            project_info.append({
                "name": project,
                "active": project == active_project,
                "card_count": card_count,
                "registered": project in state.get("projects", {})
            })
        
        return {
            "active_project": active_project,
            "projects": project_info,
            "total_projects": len(discovered_projects)
        }
    
    def _count_cards_in_project(self, project: str) -> int:
        """Count the number of cards in a specific project."""
        count = 0
        for card_file in self.glyphcards_dir.glob("*.yaml"):
            try:
                with open(card_file, 'r') as f:
                    card_data = yaml.safe_load(f)
                    if card_data.get("project") == project:
                        count += 1
            except (yaml.YAMLError, OSError):
                continue
        return count
    
    def create_project(self, project_name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new project with basic setup.
        
        Args:
            project_name: Name of the project to create
            description: Optional description for the project
            
        Returns:
            Dictionary with creation status and project information
        """
        # Validate project name
        if not project_name or not project_name.strip():
            return {
                "success": False,
                "error": "Project name cannot be empty"
            }
        
        # Clean project name (replace spaces with underscores, etc.)
        clean_name = project_name.strip().lower().replace(" ", "_").replace("-", "_")
        if clean_name != project_name:
            return {
                "success": False,
                "error": f"Project name should be '{clean_name}' (lowercase, underscores only)",
                "suggestion": clean_name
            }
        
        # Check if project already exists
        discovered_projects = self.discover_projects()
        if project_name in discovered_projects:
            return {
                "success": False,
                "error": f"Project '{project_name}' already exists",
                "existing_projects": discovered_projects
            }
        
        # Create project workspace directory
        workspace_dir = self.base_dir / "agent_workspaces" / "claude" / project_name
        workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Create basic project README
        readme_content = f"""# {project_name.replace('_', ' ').title()} Project

{description or 'Project description coming soon...'}

## Overview
This project was created using the Glyphcard project management system.

## Structure
- This directory contains all work for the `{project_name}` project
- Cards assigned to this project will build incrementally in this workspace
- All agents working on this project contribute to the same codebase

## Getting Started
Cards for this project will contain specific deliverables and validation criteria.
Follow the standard Glyphcard workflow: REORIENT → WORK → DOCUMENT → SUBMIT

Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        readme_path = workspace_dir / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        # Update project state to track this project
        state = self._load_project_state()
        state["projects"][project_name] = {
            "created": datetime.now().isoformat(),
            "description": description,
            "workspace_path": str(workspace_dir),
            "managed": True
        }
        state["last_updated"] = datetime.now().isoformat()
        self._save_project_state(state)
        
        return {
            "success": True,
            "project_name": project_name,
            "workspace_path": str(workspace_dir),
            "description": description,
            "message": f"Successfully created project '{project_name}'"
        }
    
    def activate_project(self, project_name: str) -> Dict[str, Any]:
        """Activate a specific project for the current session."""
        discovered_projects = self.discover_projects()
        
        if project_name not in discovered_projects:
            return {
                "success": False,
                "error": f"Project '{project_name}' not found",
                "available_projects": discovered_projects
            }
        
        state = self._load_project_state()
        previous_project = state.get("active_project")
        
        # Update active project
        state["active_project"] = project_name
        
        # Register project if not already registered
        if project_name not in state["projects"]:
            state["projects"][project_name] = {
                "first_activated": datetime.now().isoformat(),
                "activation_count": 1
            }
        else:
            state["projects"][project_name]["activation_count"] = \
                state["projects"][project_name].get("activation_count", 0) + 1
        
        state["projects"][project_name]["last_activated"] = datetime.now().isoformat()
        
        self._save_project_state(state)
        
        return {
            "success": True,
            "active_project": project_name,
            "previous_project": previous_project,
            "message": f"Activated project '{project_name}'",
            "card_count": self._count_cards_in_project(project_name)
        }
    
    def deactivate_project(self) -> Dict[str, Any]:
        """Deactivate the current project (enter conversation mode)."""
        state = self._load_project_state()
        previous_project = state.get("active_project")
        
        if not previous_project:
            return {
                "success": False,
                "message": "No project is currently active"
            }
        
        state["active_project"] = None
        self._save_project_state(state)
        
        return {
            "success": True,
            "deactivated_project": previous_project,
            "message": f"Deactivated project '{previous_project}'. Now in conversation mode."
        }
    
    def get_active_project(self) -> Optional[str]:
        """Get the currently active project name, if any."""
        state = self._load_project_state()
        return state.get("active_project")
    
    def is_project_active(self, project_name: str) -> bool:
        """Check if a specific project is currently active."""
        return self.get_active_project() == project_name
    
    def get_project_context(self) -> Dict[str, Any]:
        """Get complete project context for the current session."""
        state = self._load_project_state()
        active_project = state.get("active_project")
        
        context = {
            "mode": "project" if active_project else "conversation",
            "active_project": active_project,
            "timestamp": datetime.now().isoformat()
        }
        
        if active_project:
            context.update({
                "card_count": self._count_cards_in_project(active_project),
                "project_info": state["projects"].get(active_project, {})
            })
        
        return context


# CLI interface for human control
def main():
    """Command-line interface for project management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Glyphcard Project Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List projects
    list_parser = subparsers.add_parser("list", help="List all projects")
    
    # Activate project
    activate_parser = subparsers.add_parser("activate", help="Activate a project")
    activate_parser.add_argument("project", help="Project name to activate")
    
    # Deactivate project
    deactivate_parser = subparsers.add_parser("deactivate", help="Deactivate current project")
    
    # Status
    status_parser = subparsers.add_parser("status", help="Show current project status")
    
    # Create project
    create_parser = subparsers.add_parser("create", help="Create a new project")
    create_parser.add_argument("project", help="Project name to create")
    create_parser.add_argument("--description", "-d", help="Optional project description")
    
    args = parser.parse_args()
    
    pm = ProjectManager()
    
    if args.command == "list":
        result = pm.list_projects()
        print(f"\n🗂️  Project Status:")
        print(f"Active: {result['active_project'] or 'None (conversation mode)'}")
        print(f"Total Projects: {result['total_projects']}\n")
        
        for project in result["projects"]:
            status = "🟢 ACTIVE" if project["active"] else "⚪ Available"
            print(f"{status} {project['name']} ({project['card_count']} cards)")
    
    elif args.command == "activate":
        result = pm.activate_project(args.project)
        if result["success"]:
            print(f"✅ {result['message']}")
            print(f"📊 {result['card_count']} cards available in this project")
        else:
            print(f"❌ {result['error']}")
            if result.get("available_projects"):
                print("Available projects:", ", ".join(result["available_projects"]))
    
    elif args.command == "deactivate":
        result = pm.deactivate_project()
        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"ℹ️  {result['message']}")
    
    elif args.command == "status":
        context = pm.get_project_context()
        print(f"\n📋 Current Context:")
        print(f"Mode: {context['mode'].title()}")
        if context["active_project"]:
            print(f"Project: {context['active_project']}")
            print(f"Cards: {context['card_count']}")
        print(f"Updated: {context['timestamp']}\n")
    
    elif args.command == "create":
        result = pm.create_project(args.project, args.description)
        if result["success"]:
            print(f"✅ {result['message']}")
            print(f"📁 Workspace: {result['workspace_path']}")
            if result["description"]:
                print(f"📝 Description: {result['description']}")
        else:
            print(f"❌ {result['error']}")
            if result.get("suggestion"):
                print(f"💡 Suggestion: Use '{result['suggestion']}' instead")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()