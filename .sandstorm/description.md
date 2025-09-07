# Sudoku Game for Sandstorm

A complete Sudoku puzzle game that runs in your Sandstorm environment with persistent game storage.

## Features

- **Multiple Difficulty Levels**: Choose from Easy, Medium, or Hard puzzles
- **Automatic User Management**: Uses Sandstorm's built-in user authentication  
- **Persistent Storage**: All games are automatically saved to your grain
- **Real-time Validation**: Instant feedback on moves with conflict detection
- **Timer Tracking**: See how long each puzzle takes to complete
- **Responsive Design**: Works great on desktop and mobile devices

## How to Play

1. Select your preferred difficulty level
2. Click on empty cells and enter numbers 1-9
3. Follow standard Sudoku rules: each row, column, and 3×3 box must contain all digits 1-9
4. Games are automatically saved as you play
5. Use the validate button to check for conflicts
6. Complete the puzzle and celebrate your success!

## Sandstorm Integration

This app is fully integrated with Sandstorm's security model:

- **No User Accounts**: Uses your Sandstorm identity automatically
- **Secure Storage**: All game data is isolated to your grain
- **Permission-based Access**: Respects Sandstorm's sharing permissions
- **Capability Security**: Cannot access data from other apps or users

## Technical Details

- Built with Python Flask backend and JavaScript frontend
- SQLite database for persistent game storage
- RESTful API design for clean separation of concerns
- Mobile-responsive CSS with modern design patterns
