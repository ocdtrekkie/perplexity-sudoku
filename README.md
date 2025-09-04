# Sudoku Flask Game

A complete Sudoku web application built with Flask backend and JavaScript frontend, featuring SQLite database storage for game persistence.

## Features

- **Multiple Difficulty Levels**: Easy, Medium, and Hard
- **Database Persistence**: All games are saved to SQLite database
- **Session Management**: Track games per user session
- **Real-time Validation**: Instant feedback on moves
- **Timer**: Track time spent on each puzzle
- **Save/Load Games**: Resume games anytime
- **Auto-save**: Games are automatically saved after each move
- **Hint System**: Get help when stuck
- **Responsive Design**: Works on desktop and mobile

## Installation

1. **Clone or download the files**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python run.py
   ```

4. **Open your browser** and visit: `http://127.0.0.1:5000`

## API Endpoints

- `POST /api/new-game` - Create a new Sudoku puzzle
- `GET /api/game/<id>` - Load a specific game
- `PUT /api/game/<id>` - Save game progress  
- `GET /api/games` - List user's saved games
- `POST /api/validate` - Validate current board state

## Database Schema

The application uses SQLite with the following table:

```sql
CREATE TABLE sudoku_game (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_session_id VARCHAR(100) NOT NULL,
    board_state TEXT NOT NULL,
    original_puzzle TEXT NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    is_complete BOOLEAN DEFAULT FALSE,
    time_spent INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## How to Play

1. **Choose Difficulty**: Select Easy (40 filled), Medium (32 filled), or Hard (26 filled)
2. **Fill the Grid**: Click cells and enter numbers 1-9
3. **Follow Sudoku Rules**: Each row, column, and 3×3 box must contain digits 1-9
4. **Get Hints**: Click hint button for valid numbers in selected cell
5. **Save Progress**: Games auto-save, or manually save anytime
6. **Load Games**: View and resume saved games from the sidebar

## Technical Details

- **Backend**: Flask with SQLAlchemy ORM
- **Database**: SQLite for persistence
- **Frontend**: Vanilla JavaScript with modern ES6+ features
- **Styling**: Custom CSS with responsive design
- **Session Management**: Flask sessions for user tracking
- **CORS**: Enabled for API access
- **Game Logic**: Complete Sudoku generation and validation

## File Structure

```
sudoku_flask_app/
├── app.py                 # Main Flask application
├── run.py                 # Application runner
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Main HTML template
└── static/
    ├── css/
    │   └── style.css     # Stylesheet
    └── js/
        └── sudoku.js     # JavaScript game logic
```

## Development

To extend the application:

1. **Add new difficulty levels** in `SudokuGenerator` class
2. **Implement user authentication** for persistent user accounts
3. **Add multiplayer features** with WebSocket support
4. **Create game statistics** and progress tracking
5. **Add puzzle importing** from external sources

## Browser Compatibility

- Chrome/Edge 60+
- Firefox 55+
- Safari 12+
- Mobile browsers with ES6 support

Enjoy playing Sudoku!
