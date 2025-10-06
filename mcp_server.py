#!/usr/bin/env python3
"""
Glyphcard Workflow Automation MCP Server
A Model Context Protocol server that enables Claude Code CLI to automatically 
follow the four-step Glyphcard process without constant human reminders.

This server provides Glyphcard-specific workflow tools for:
- Discovering available work
- Starting card reorientation
- Getting orientation context  
- Validating deliverables
- Submitting completed work
- Managing workflow state
"""

from fastmcp import FastMCP
import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the orientation directory to the path so we can import the existing scripts
BASE_DIR = Path(__file__).parent
ORIENTATION_DIR = BASE_DIR / "orientation"
sys.path.append(str(ORIENTATION_DIR))

# Dependency helpers
from dependency_manager import compute_dependency_state
from create_card_ai import create_card as create_card_ai
from project_manager import ProjectManager
from archive_manager import ArchiveManager

# Create the MCP server instance
mcp = FastMCP(
    name="Glyphcard Workflow Automation Server",
    version="2.0.0",
    instructions="A FastMCP server providing Glyphcard workflow automation tools for Claude Code CLI"
)

class GlyphcardWorkflow:
    """Core workflow management class for Glyphcard automation."""
    
    def __init__(self):
        self.base_dir = BASE_DIR
        self.glyphcards_dir = self.base_dir / "glyphcards"
        self.orientation_dir = self.base_dir / "orientation"
        self.system_state_file = self.orientation_dir / "system_state.json"
        self.acceptance_file = self.base_dir / "acceptance.yaml"
        self.current_agent = "claude"  # Default agent
        self.project_manager = ProjectManager(self.base_dir)  # Project activation system
        self.archive_manager = ArchiveManager(self.base_dir)  # Archive management system
        
    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file safely."""
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load JSON file safely."""
        with open(path, 'r') as f:
            return json.load(f)
    
    def _save_yaml(self, data: Dict[str, Any], path: Path) -> None:
        """Save data to YAML file."""
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

# Create global workflow instance
workflow = GlyphcardWorkflow()

@mcp.tool
def health_check() -> Dict[str, Any]:
    """Health check endpoint to verify the workflow automation server is running correctly."""
    return {
        "status": "healthy",
        "service": "glyphcard-workflow-automation-server",
        "version": "2.0.0",
        "working_directory": str(Path.cwd()),
        "server_name": "Glyphcard Workflow Automation Server",
        "agent": workflow.current_agent
    }

def _get_orientation_context_internal(card_id: str) -> Dict[str, Any]:
    """Internal helper to get orientation context without decorator conflicts."""
    try:
        packet_file = workflow.orientation_dir / f"orientation_packet_{card_id}.yaml"
        
        if not packet_file.exists():
            return {
                "error": f"Orientation packet not found for card {card_id}. Run glyphcard_start_card first.",
                "card_id": card_id
            }
        
        packet = workflow._load_yaml(packet_file)
        
        # Parse review notes if they exist
        review_notes_summary = ""
        if packet.get("review_notes"):
            latest_review = packet["review_notes"][-1]  # Get most recent review
            review_notes_summary = latest_review.get("notes", "")[:500] + "..." if len(latest_review.get("notes", "")) > 500 else latest_review.get("notes", "")
        
        return {
            "card_id": packet.get("card_id"),
            "title": packet.get("title"),
            "deliverables": packet.get("deliverables", []),
            "validation": packet.get("validation", []),
            "context_needs": packet.get("context_brief", {}).get("context_needs", []),
            "open_questions": packet.get("open_questions", []),
            "has_review_notes": bool(packet.get("review_notes")),
            "review_notes_summary": review_notes_summary,
            "linked_modules": packet.get("context_brief", {}).get("linked_modules", {}),
            "packet_path": str(packet_file)
        }
        
    except Exception as e:
        return {"error": f"Failed to get orientation context for card {card_id}: {str(e)}"}

@mcp.tool
def check_dependencies(card_id: str) -> Dict[str, Any]:
    """Verify linked cards and prerequisites are met for a card.
    
    Dependencies are met only when prerequisite cards are ACCEPTED, not just completed.
    This enforces the human review process in the workflow.
    
    Args:
        card_id: The ID of the card to check dependencies for
    """
    try:
        dependency_state, card_entries = compute_dependency_state()
        lookup: Dict[Any, Dict[str, Any]] = {}
        for entry in card_entries:
            key = entry["id"] if entry["id"] is not None else entry["id_str"]
            lookup[key] = entry

        key = int(card_id) if str(card_id).isdigit() else str(card_id)
        entry = lookup.get(key)
        if not entry:
            alt_key = str(card_id).zfill(3)
            entry = lookup.get(alt_key)
        if not entry:
            return {"error": f"Card {card_id} not found"}

        dep_info = dependency_state.get(key) or dependency_state.get(str(card_id).zfill(3)) or {}
        dependencies: List[Dict[str, Any]] = []
        all_met = not dep_info.get("blocked", False)

        for parent_id in dep_info.get("parents", []):
            parent_entry = lookup.get(parent_id) or (
                lookup.get(int(parent_id)) if parent_id.isdigit() else None
            )
            parent_status = parent_entry["data"].get("status", "unknown") if parent_entry else "unknown"
            is_missing = parent_id in dep_info.get("missing_parents", [])
            is_pending = parent_id in dep_info.get("pending_parents", [])
            is_met = not dep_info.get("blocked", False) or (not is_missing and not is_pending and parent_status == "accepted")

            if is_missing:
                explanation = "Linked card file not found"
                is_met = False
            elif is_pending:
                explanation = "Submitted but awaiting human acceptance"
                is_met = False
            elif parent_status == "accepted":
                explanation = "Accepted by human reviewer"
                is_met = True
            else:
                explanation = f"Card status is '{parent_status}' but not accepted"
                is_met = False

            dependencies.append({
                "type": "linked_card",
                "card_id": parent_id,
                "title": parent_entry["data"].get("title", "Unknown") if parent_entry else "Unknown",
                "card_status": parent_status,
                "acceptance_status": "accepted" if is_met else ("pending" if is_pending else "not_accepted"),
                "met": is_met,
                "explanation": explanation,
            })

            if not is_met:
                all_met = False

        context = _get_orientation_context_internal(card_id)
        if "error" not in context:
            linked_modules = context.get("linked_modules", {})
            for module_name, module_info in linked_modules.items():
                status = module_info.get("status", "unknown")
                is_met = status == "completed"
                dependencies.append({
                    "type": "module",
                    "module_name": module_name,
                    "status": status,
                    "linked_cards": module_info.get("linked_cards", []),
                    "met": is_met,
                    "explanation": f"Module status: {status}"
                })
                if not is_met:
                    all_met = False

        return {
            "card_id": card_id,
            "dependencies_met": all_met,
            "dependencies": dependencies,
            "workflow_note": "Dependencies require human acceptance, not just completion, to maintain review quality control"
        }

    except Exception as e:
        return {"error": f"Failed to check dependencies for card {card_id}: {str(e)}"}

@mcp.tool
def create_card(
    title: str,
    deliverables: List[str],
    project: Optional[str] = None,
    context_needs: Optional[List[str]] = None,
    validation: Optional[List[str]] = None,
    open_questions: Optional[List[str]] = None,
    linked_to: Optional[str] = None,
    assigned_to: str = "claude",
    size: str = "2-4 hours"
) -> Dict[str, Any]:
    """Create a new glyphcard with specified details.
    
    Args:
        title: The title/name of the card
        deliverables: List of deliverables for this card
        project: Project name (defaults to active project if in project mode)
        context_needs: List of context requirements (optional)
        validation: List of validation criteria (optional)
        open_questions: List of open questions (optional)
        linked_to: ID of prerequisite card (optional)
        assigned_to: Who the card is assigned to (default: claude)
        size: Estimated time to complete (default: 2-4 hours)
    
    Returns:
        Dictionary with success status and card details
    """
    try:
        # Use the create_card_ai module to create the card
        card_path = create_card_ai(
            title=title,
            project=project,
            assigned_to=assigned_to,
            size=size,
            context_needs=context_needs or [],
            deliverables=deliverables,
            validation=validation or [],
            open_questions=open_questions or [],
            linked_to=linked_to
        )
        
        # Parse the created card to get details
        card_data = workflow._load_yaml(Path(card_path))
        
        return {
            "success": True,
            "card_id": card_data.get("id"),
            "title": card_data.get("title"),
            "status": card_data.get("status"),
            "project": card_data.get("project"),
            "file_path": card_path,
            "message": f"Successfully created card {card_data.get('id'):03d}: {title}"
        }
        
    except Exception as e:
        return {"error": f"Failed to create card: {str(e)}"}

# Enhanced API Layer - Streamlined interfaces for AI agents

def _discover_available_work_internal() -> Dict[str, Any]:
    """Internal implementation of work discovery."""
    try:
        available_cards: List[Dict[str, Any]] = []
        blocked_cards: List[Dict[str, Any]] = []

        dependency_state, card_entries = compute_dependency_state()
        index_by_key: Dict[Any, Dict[str, Any]] = {}
        for entry in card_entries:
            key = entry["id"] if entry["id"] is not None else entry["id_str"]
            index_by_key[key] = entry

        def lookup_entry(identifier: str) -> Optional[Dict[str, Any]]:
            if identifier in index_by_key:
                return index_by_key[identifier]
            if identifier.isdigit():
                return index_by_key.get(int(identifier))
            return None

        for entry in card_entries:
            card = entry["data"]

            if card.get("assigned_to") != workflow.current_agent:
                continue

            # Project namespace filtering - only show cards from active project
            active_project = workflow.project_manager.get_active_project()
            if active_project:
                # In project mode - filter to only cards in the active project
                if card.get("project") != active_project:
                    continue
            # In conversation mode - show all cards (no filtering)

            status = card.get("status", "")
            if status not in ["assigned", "needs_revision", "available", "in_progress"]:
                continue

            key = entry["id"] if entry["id"] is not None else entry["id_str"]
            dep_info = dependency_state.get(key, {"blocked": False, "parents": []})
            dependencies_met = not dep_info.get("blocked", False)

            card_info = {
                "id": card.get("id"),
                "title": card.get("title", ""),
                "status": status,
                "size": card.get("size", "unknown"),
                "project": card.get("project", "unknown"),
                "has_review_notes": bool(card.get("review_notes"))
            }

            if dependencies_met:
                available_cards.append(card_info)
            else:
                blocked_cards.append(card_info)
        
        return {
            "available_cards": available_cards,
            "blocked_cards": blocked_cards,
            "count": len(available_cards),
            "blocked_count": len(blocked_cards)
        }
        
    except Exception as e:
        return {"error": f"Failed to discover available work: {str(e)}"}

@mcp.tool
def start_work() -> Dict[str, Any]:
    """
    Simple command to discover and start the next available card automatically.
    Returns:
        Simple response with next action or work started
    """
    try:
        # Discover available work
        work = _discover_available_work_internal()
        
        if "error" in work:
            return {"action": "error", "message": work["error"]}
        
        available = work.get("available_cards", [])
        
        if not available:
            blocked = work.get("blocked_cards", [])
            if blocked:
                return {
                    "action": "waiting", 
                    "message": f"No work available. {len(blocked)} cards blocked by dependencies.",
                    "suggestion": "Check blocked cards or create a new card"
                }
            else:
                return {
                    "action": "no_work",
                    "message": "No cards assigned to you. Create a new card to get started.",
                    "suggestion": "Use create_card to create new work"
                }
        
        # Start the first available card
        next_card = available[0]
        card_id = str(next_card["id"])
        
        # Format card ID with zero padding for filename matching
        padded_card_id = str(next_card["id"]).zfill(3)
        
        # Run the reorienter script
        result = subprocess.run([
            sys.executable,
            str(workflow.orientation_dir / "reorienter.py"),
            "--card", padded_card_id
        ], capture_output=True, text=True, cwd=str(workflow.base_dir))

        if result.returncode != 0:
            return {"action": "error", "message": f"Failed to start card: {result.stderr}"}

        return {
            "action": "started",
            "card_id": card_id,
            "title": next_card["title"],
            "message": f"Started work on Card {card_id}: {next_card['title']}",
            "next_step": "Use get_card_context to see what you need to do",
            "workflow_reminder": {
                "current_phase": "1. REORIENT ✅ (completed)",
                "next_phases": [
                    "2. WORK - Implement deliverables in agent_workspaces/{agent}/{project}/",
                    "3. DOCUMENT - Create output_{card_id}.md with summary, deliverables, validation",
                    "4. SUBMIT - Call submit_card() when documentation is complete"
                ],
                "important": "Documentation is mandatory before submission. The submit_card() tool will validate it exists."
            }
        }
        
    except Exception as e:
        return {"action": "error", "message": f"Failed to start work: {str(e)}"}

@mcp.tool
def get_card_context(card_id: str) -> Dict[str, Any]:
    """
    Get everything you need to know about a card in a clean, actionable format.
    Args:
        card_id: The card ID to get context for

    Returns:
        Clean context with what to do, what to deliver, and how to validate
    """
    try:
        context = _get_orientation_context_internal(card_id)

        if "error" in context:
            return {"error": context["error"]}

        # Check progress on the card
        padded_card_id = str(card_id).zfill(3)
        orientation_packet = workflow.orientation_dir / f"orientation_packet_{padded_card_id}.yaml"
        output_file = workflow.base_dir / "agent_workspaces" / workflow.current_agent / f"output_{padded_card_id}.md"

        # Build progress checklist
        progress = {
            "reoriented": orientation_packet.exists(),
            "documentation_exists": output_file.exists(),
            "documentation_length": len(output_file.read_text()) if output_file.exists() else 0,
            "ready_to_submit": output_file.exists() and len(output_file.read_text()) > 200
        }

        # Determine next recommended action
        if not progress["documentation_exists"]:
            next_action = "Implement deliverables, then create output_{card_id}.md documentation"
        elif not progress["ready_to_submit"]:
            next_action = "Complete documentation in output_{card_id}.md"
        else:
            next_action = "Review work and call submit_card() when ready"

        # Streamlined response focused on action
        return {
            "card_id": context["card_id"],
            "title": context["title"],
            "what_to_build": context.get("deliverables", []),
            "how_to_validate": context.get("validation", []),
            "context_you_need": context.get("context_needs", []),
            "questions_to_resolve": context.get("open_questions", []),
            "has_feedback": context.get("has_review_notes", False),
            "feedback_summary": context.get("review_notes_summary", "") if context.get("has_review_notes") else None,
            "progress": progress,
            "next_recommended_action": next_action,
            "ready_to_code": True
        }

    except Exception as e:
        return {"error": f"Failed to get context: {str(e)}"}

@mcp.tool
def submit_card(card_id: str, module_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Submit completed work including mandatory documentation phase.
    Args:
        card_id: The card ID to submit
        module_name: Optional module name (auto-generated if not provided)

    Returns:
        Simple success/failure response
    """
    try:
        # Validate documentation exists (mandatory step)
        padded_card_id = str(card_id).zfill(3)
        output_file = workflow.base_dir / "agent_workspaces" / workflow.current_agent / f"output_{padded_card_id}.md"

        if not output_file.exists():
            return {
                "success": False,
                "error": "Documentation required before submission",
                "message": f"Please create output_{padded_card_id}.md before submitting.",
                "required_sections": [
                    "## Summary - What you completed",
                    "## Deliverables - Checklist with ✅/❌ status",
                    "## Validation - How you verified it works",
                    "## Files Modified - List of changed files with paths",
                    "## Handoff Notes - Any issues or next steps"
                ],
                "documentation_path": str(output_file),
                "next_step": "Create the documentation file and try submit_card again"
            }

        # Check documentation quality (warning, not blocker)
        doc_content = output_file.read_text()
        doc_length = len(doc_content.strip())

        warnings = []
        if doc_length < 200:
            warnings.append(f"Documentation is brief ({doc_length} chars). Consider adding more detail about what you built and how to validate it.")

        if "##" not in doc_content:
            warnings.append("Documentation has no section headers. Consider using ## Summary, ## Deliverables, etc.")

        # Auto-generate module name if not provided
        if module_name is None:
            context = _get_orientation_context_internal(card_id)
            if "error" not in context:
                title = context.get("title", "").lower().replace(" ", "_")
                module_name = f"card_{card_id}_{title}"
            else:
                module_name = f"card_{card_id}_output"

        # Run the submit_output script
        result = subprocess.run([
            sys.executable,
            str(workflow.orientation_dir / "submit_output.py"),
            "--card", padded_card_id,
            "--module", module_name
        ], capture_output=True, text=True, cwd=str(workflow.base_dir))

        if result.returncode != 0:
            return {"success": False, "message": f"Submission failed: {result.stderr}"}

        response = {
            "success": True,
            "card_id": card_id,
            "module": module_name,
            "message": f"Card {card_id} submitted successfully! Awaiting human review.",
            "next_action": "Work is now in review queue. You can start work on another card."
        }

        if warnings:
            response["warnings"] = warnings

        return response

    except Exception as e:
        return {"success": False, "message": f"Failed to submit: {str(e)}"}

@mcp.tool
def list_my_work() -> Dict[str, Any]:
    """
    Show all work assigned to me in an easy to understand format.
    Returns:
        List view of available and blocked cards.
    """
    try:
        work = _discover_available_work_internal()
        
        if "error" in work:
            return {"error": work["error"]}
        
        available = work.get("available_cards", [])
        blocked = work.get("blocked_cards", [])
        
        # Simplify the output
        simple_available = [
            {
                "id": card["id"],
                "title": card["title"], 
                "size": card["size"],
                "project": card["project"]
            }
            for card in available
        ]
        
        simple_blocked = [
            {
                "id": card["id"],
                "title": card["title"]
            }
            for card in blocked
        ]
        
        return {
            "available_now": simple_available,
            "blocked": simple_blocked,
            "summary": f"{len(simple_available)} cards ready, {len(simple_blocked)} blocked",
            "suggestion": "Use start_work() to begin the next available card"
        }
        
    except Exception as e:
        return {"error": f"Failed to list work: {str(e)}"}

# Project Activation and Namespace Management Tools

@mcp.tool
def list_projects() -> Dict[str, Any]:
    """
    List all available projects with status information.
    Shows active project, card counts, and project registration status.
    
    Returns:
        Dictionary with project information and current status
    """
    try:
        return workflow.project_manager.list_projects()
    except Exception as e:
        return {"error": f"Failed to list projects: {str(e)}"}

@mcp.tool  
def activate_project(project_name: str) -> Dict[str, Any]:
    """
    Activate a specific project for the current session.
    This switches the context to focus on cards within the specified project.
    
    Args:
        project_name: Name of the project to activate
        
    Returns:
        Dictionary with activation status and project information
    """
    try:
        return workflow.project_manager.activate_project(project_name)
    except Exception as e:
        return {"error": f"Failed to activate project: {str(e)}"}

@mcp.tool
def deactivate_project() -> Dict[str, Any]:
    """
    Deactivate the current project and return to conversation mode.
    In conversation mode, all cards across all projects are visible.
    
    Returns:
        Dictionary with deactivation status
    """
    try:
        return workflow.project_manager.deactivate_project()
    except Exception as e:
        return {"error": f"Failed to deactivate project: {str(e)}"}

@mcp.tool
def get_project_context() -> Dict[str, Any]:
    """
    Get complete project context for the current session.
    Shows whether in project mode or conversation mode, active project, and metadata.
    
    Returns:
        Dictionary with current project context and session information
    """
    try:
        return workflow.project_manager.get_project_context()
    except Exception as e:
        return {"error": f"Failed to get project context: {str(e)}"}

@mcp.tool
def create_project(project_name: str, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new project with basic workspace setup.
    
    Args:
        project_name: Name of the project (lowercase, underscores only)
        description: Optional description for the project
        
    Returns:
        Dictionary with creation status and project information
    """
    try:
        return workflow.project_manager.create_project(project_name, description)
    except Exception as e:
        return {"error": f"Failed to create project: {str(e)}"}

# Archive Management Tools

@mcp.tool
def archive_card(card_id: str) -> Dict[str, Any]:
    """
    Archive an accepted card and its related files.  
    Args:
        card_id: The ID of the card to archive
    Returns:
        Dictionary with archival status and details
    """
    try:
        return workflow.archive_manager.archive_card(card_id)
    except Exception as e:
        return {"error": f"Failed to archive card: {str(e)}"}

@mcp.tool
def cleanup_acceptance_tracking() -> Dict[str, Any]:
    """
    Remove archived cards from acceptance.yaml tracking.
    Returns:
        Dictionary with cleanup status and details
    """
    try:
        return workflow.archive_manager.cleanup_acceptance_tracking()
    except Exception as e:
        return {"error": f"Failed to cleanup acceptance tracking: {str(e)}"}

@mcp.tool
def list_archived_cards() -> Dict[str, Any]:
    """
    List all archived cards.   
    Returns:
        Dictionary with archived card information
    """
    try:
        return workflow.archive_manager.list_archived_cards()
    except Exception as e:
        return {"error": f"Failed to list archived cards: {str(e)}"}

if __name__ == "__main__":
    mcp.run()
