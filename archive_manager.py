#!/usr/bin/env python3
"""
Archive Management System for Glyphcard
Handles archiving of accepted cards and cleanup of acceptance tracking.
"""

import os
import yaml
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class ArchiveManager:
    """Manages archiving of accepted glyphcards and related cleanup."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).parent
        self.glyphcards_dir = self.base_dir / "glyphcards"
        self.acceptance_file = self.base_dir / "acceptance.yaml"
        self.archive_dir = self.base_dir / "archive" / "glyphcards"
        self.system_state_file = self.base_dir / "orientation" / "system_state.json"
        
        # Ensure archive directory exists
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file safely."""
        if not path.exists():
            return {}
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def _save_yaml(self, data: Dict[str, Any], path: Path) -> None:
        """Save data to YAML file."""
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def archive_card(self, card_id: str) -> Dict[str, Any]:
        """Archive a specific card and its related files.
        
        Args:
            card_id: The ID of the card to archive
            
        Returns:
            Dictionary with archival status and details
        """
        try:
            # Format card ID with zero padding
            padded_card_id = str(card_id).zfill(3)
            
            # Find the card file
            card_file = None
            for pattern in [f"{padded_card_id}_*.yaml", f"{card_id}_*.yaml"]:
                matches = list(self.glyphcards_dir.glob(pattern))
                if matches:
                    card_file = matches[0]
                    break
            
            if not card_file:
                return {
                    "success": False,
                    "error": f"Card {card_id} not found in glyphcards directory"
                }
            
            # Load card data to check status
            card_data = self._load_yaml(card_file)
            if card_data.get("status") != "accepted":
                return {
                    "success": False,
                    "error": f"Card {card_id} is not accepted (status: {card_data.get('status', 'unknown')})",
                    "suggestion": "Only accepted cards can be archived"
                }
            
            # Move card file to archive
            archive_path = self.archive_dir / card_file.name
            shutil.move(str(card_file), str(archive_path))
            
            # Archive related output files
            archived_files = [str(archive_path)]
            output_patterns = [
                f"agent_workspaces/*/output_{padded_card_id}.md",
                f"agent_workspaces/*/output_{card_id}.md",
                f"agents/*/task_{padded_card_id}_output.md",
                f"agents/*/task_{card_id}_output.md"
            ]
            
            for pattern in output_patterns:
                for output_file in self.base_dir.glob(pattern):
                    if output_file.exists():
                        # Create archive subdirectory for outputs
                        output_archive_dir = self.archive_dir / "outputs"
                        output_archive_dir.mkdir(exist_ok=True)
                        
                        # Move output file
                        archive_output_path = output_archive_dir / output_file.name
                        shutil.move(str(output_file), str(archive_output_path))
                        archived_files.append(str(archive_output_path))
            
            return {
                "success": True,
                "card_id": card_id,
                "archived_files": archived_files,
                "archive_location": str(archive_path),
                "message": f"Successfully archived card {card_id}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to archive card {card_id}: {str(e)}"
            }
    
    def cleanup_acceptance_tracking(self) -> Dict[str, Any]:
        """Remove archived cards from acceptance.yaml tracking.
        
        Returns:
            Dictionary with cleanup status and details
        """
        try:
            # Get list of archived card IDs
            archived_ids = set()
            if self.archive_dir.exists():
                for archived_file in self.archive_dir.glob("*.yaml"):
                    # Extract card ID from filename (format: 001_title.yaml)
                    filename_parts = archived_file.stem.split('_', 1)
                    if filename_parts:
                        card_id = filename_parts[0].lstrip('0') or '0'  # Remove leading zeros
                        archived_ids.add(card_id)
            
            # Load acceptance data
            acceptance_data = self._load_yaml(self.acceptance_file)
            
            # Clean up accepted list
            original_accepted = acceptance_data.get('accepted', [])
            cleaned_accepted = [
                card for card in original_accepted
                if card.get('id', '').lstrip('0') not in archived_ids and card.get('id') not in archived_ids
            ]
            
            # Clean up pending reviews (shouldn't happen, but just in case)
            original_pending = acceptance_data.get('pending_reviews', [])
            cleaned_pending = [
                card for card in original_pending
                if card.get('id', '').lstrip('0') not in archived_ids and card.get('id') not in archived_ids
            ]
            
            # Update acceptance data
            acceptance_data['accepted'] = cleaned_accepted
            acceptance_data['pending_reviews'] = cleaned_pending
            
            # Calculate cleanup stats
            removed_accepted = len(original_accepted) - len(cleaned_accepted)
            removed_pending = len(original_pending) - len(cleaned_pending)
            total_removed = removed_accepted + removed_pending
            
            # Save if anything was cleaned up
            if total_removed > 0:
                self._save_yaml(acceptance_data, self.acceptance_file)
            
            return {
                "success": True,
                "removed_accepted": removed_accepted,
                "removed_pending": removed_pending,
                "total_removed": total_removed,
                "archived_count": len(archived_ids),
                "message": f"Cleaned up {total_removed} archived cards from acceptance tracking"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to cleanup acceptance tracking: {str(e)}"
            }
    
    def list_archived_cards(self) -> Dict[str, Any]:
        """List all archived cards.
        
        Returns:
            Dictionary with archived card information
        """
        try:
            archived_cards = []
            
            if self.archive_dir.exists():
                for archived_file in self.archive_dir.glob("*.yaml"):
                    try:
                        card_data = self._load_yaml(archived_file)
                        archived_cards.append({
                            "id": card_data.get("id"),
                            "title": card_data.get("title", "Unknown"),
                            "project": card_data.get("project", "Unknown"),
                            "archived_date": archived_file.stat().st_mtime,
                            "filename": archived_file.name
                        })
                    except Exception:
                        continue
            
            # Sort by ID
            archived_cards.sort(key=lambda x: int(x["id"]) if x["id"] and str(x["id"]).isdigit() else 0)
            
            return {
                "success": True,
                "archived_cards": archived_cards,
                "count": len(archived_cards),
                "archive_location": str(self.archive_dir)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list archived cards: {str(e)}"
            }

def main():
    """CLI interface for archive management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Glyphcard Archive Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Archive card
    archive_parser = subparsers.add_parser("archive", help="Archive a specific card")
    archive_parser.add_argument("card_id", help="Card ID to archive")
    
    # Cleanup acceptance
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up acceptance tracking")
    
    # List archived
    list_parser = subparsers.add_parser("list", help="List archived cards")
    
    args = parser.parse_args()
    
    archive_manager = ArchiveManager()
    
    if args.command == "archive":
        result = archive_manager.archive_card(args.card_id)
        if result["success"]:
            print(f"✅ {result['message']}")
            print(f"📁 Archived to: {result['archive_location']}")
            if len(result['archived_files']) > 1:
                print(f"📄 Total files archived: {len(result['archived_files'])}")
        else:
            print(f"❌ {result['error']}")
            if result.get("suggestion"):
                print(f"💡 {result['suggestion']}")
    
    elif args.command == "cleanup":
        result = archive_manager.cleanup_acceptance_tracking()
        if result["success"]:
            if result["total_removed"] > 0:
                print(f"✨ {result['message']}")
                print(f"📊 Removed {result['removed_accepted']} accepted, {result['removed_pending']} pending")
            else:
                print("✅ No archived cards to clean up from acceptance tracking")
        else:
            print(f"❌ {result['error']}")
    
    elif args.command == "list":
        result = archive_manager.list_archived_cards()
        if result["success"]:
            print(f"\n📦 Archived Cards ({result['count']} total):")
            print(f"Location: {result['archive_location']}\n")
            for card in result["archived_cards"]:
                print(f"Card {card['id']:>3}: {card['title']} (Project: {card['project']})")
            if result['count'] == 0:
                print("No cards archived yet.")
        else:
            print(f"❌ {result['error']}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()