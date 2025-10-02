# Cat Picture App

A simple web application that displays random cat pictures to brighten your day!

## Overview
This project demonstrates a clean, simple web app architecture with a frontend for displaying cat images and a backend API for serving data.

## Project Structure
```
cat-picture-app/
├── frontend/          # Client-side application
│   ├── index.html    # Main HTML page
│   ├── styles.css    # Styling
│   └── script.js     # JavaScript functionality
├── backend/          # Server-side API (future development)
└── README.md         # This file
```

## Getting Started

### Option 1: Direct File Access
1. Clone this repository
2. Navigate to the `frontend/` directory
3. Open `index.html` in your web browser:
   - **Windows**: Double-click `index.html` or drag it to your browser
   - **Linux/WSL**: Use `xdg-open frontend/index.html` or `wslview frontend/index.html` 
   - **macOS**: Use `open frontend/index.html`
   - **Any OS**: Right-click `index.html` → "Open with" → Choose your browser

### Option 2: Local Server (Recommended)
For the best experience, serve the files via HTTP:
```bash
# Navigate to the frontend directory
cd frontend/

# Python 3
python -m http.server 8000

# Then open: http://localhost:8000
```

### Option 3: VS Code Live Server
1. Install the "Live Server" extension in VS Code
2. Right-click on `frontend/index.html`
3. Select "Open with Live Server"

**Note**: Some features may require HTTP serving due to browser security restrictions.

## Development
- Frontend: Vanilla HTML, CSS, and JavaScript
- Backend: To be determined (see Card 002)

## Contributing
This project uses a Glyphcard workflow system. Check the glyphcards/ directory for current tasks and assignments.

## License
MIT License - feel free to use and modify!