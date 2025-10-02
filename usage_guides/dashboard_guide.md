# Glyphcard PM Dashboard

A lightweight web interface for managing card acceptance in Glyphcard.

## Features

- **Visual Task Queue**: See all tasks awaiting acceptance at a glance
- **Rich Context**: View deliverables, validation criteria, and output previews
- **Quick Actions**: Accept tasks or request changes with one click
- **Revision Notes**: Add detailed feedback when requesting changes
- **Task Archiving**: Archive accepted tasks to keep the queue clean
- **Responsive Design**: Works on desktop and mobile

## Starting the Dashboard

```bash
# Glyphcard PM Dashboard

A lightweight web interface for managing card acceptance in the Glyphcard system.

## Features

- **Visual Card Queue**: See all cards awaiting acceptance at a glance
- **Rich Context**: View deliverables, validation criteria, and output previews
- **Quick Actions**: Accept cards or request changes with one click
- **Revision Notes**: Add detailed feedback when requesting changes
- **Card Archiving**: Archive accepted cards to keep the queue clean
- **Responsive Design**: Works on desktop and mobile

## Starting the Dashboard

```bash
./start_dashboard.sh
```

Then open http://localhost:5000 in your browser.

## Usage

1. **Pending Cards**: Shows all cards marked as `awaiting_acceptance`
   - Click ✅ Accept to approve the card
   - Click 🔁 Request Changes to add revision notes
   - Expandable sections show deliverables, validation criteria, and output

2. **Cards Needing Revision**: Shows cards where changes were requested
   - Displays the revision notes for the assignee to address

3. **Recently Accepted**: Shows the last 10 accepted cards
   - Click 📦 Archive to move completed cards to the archive folder

## Card Flow

1. AI completes card → Status: `awaiting_acceptance`
2. PM reviews in dashboard → Accept or Request Changes
3. If accepted → Status: `accepted` ✅
4. If changes needed → Status: `needs_revision` with notes
5. AI addresses feedback → Resubmits → Back to step 1

## Archive

Archived cards are moved to `/archive/glyphcards/` to keep the main glyphcards folder organized.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Copyright (c) 2025 Megan Folsom**