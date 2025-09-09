import os
import json
import random
import copy
from datetime import datetime
from urllib.parse import unquote

from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Sandstorm Configuration
def create_sandstorm_app():
    """Create Flask app configured for Sandstorm.io"""

    # In Sandstorm, the writable storage is at /var
    instance_path = '/var'

    app = Flask(__name__, instance_path=instance_path)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sandstorm-sudoku-secret-key')

    # Database configuration - Sandstorm apps store data in /var
    db_path = os.path.join(instance_path, 'sudoku_games.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Ensure /var directory exists and is writable
    try:
        os.makedirs(instance_path, exist_ok=True)
        # Test write permissions
        test_file = os.path.join(instance_path, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print(f"Database will be stored at: {db_path}")
    except (OSError, IOError) as e:
        print(f"Warning: Cannot write to {instance_path}: {e}")

    return app

# Create the app instance
app = create_sandstorm_app()

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# Sandstorm User Management
class SandstormUser:
    """Helper class for managing Sandstorm user information"""

    @staticmethod
    def get_user_id(request):
        """Get the Sandstorm user ID from HTTP headers"""
        user_id = request.headers.get('X-Sandstorm-User-Id')
        if not user_id:
            # For testing outside Sandstorm, use a default user
            user_id = 'dev-user-' + request.remote_addr.replace('.', '-')
        return user_id

    @staticmethod
    def get_preferred_handle(request):
        """Get the user's preferred handle from HTTP headers"""
        handle = request.headers.get('X-Sandstorm-Preferred-Handle')
        if not handle:
            # Fallback for development/testing
            handle = request.headers.get('X-Sandstorm-Username', 'Anonymous User')
            # Decode percent-encoded username if present
            if handle:
                try:
                    handle = unquote(handle)
                except:
                    pass
        return handle or 'Anonymous User'

    @staticmethod
    def get_permissions(request):
        """Get user permissions from Sandstorm headers"""
        permissions = request.headers.get('X-Sandstorm-Permissions', '')
        return permissions.split(',') if permissions else []

    @staticmethod
    def has_permission(request, permission):
        """Check if user has a specific permission"""
        return permission in SandstormUser.get_permissions(request)

# Database Models
class SudokuGame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sandstorm_user_id = db.Column(db.String(100), nullable=False, index=True)  # Sandstorm User ID
    user_handle = db.Column(db.String(200))  # Display name for user
    board_state = db.Column(db.Text, nullable=False)  # JSON string
    original_puzzle = db.Column(db.Text, nullable=False)  # JSON string
    difficulty = db.Column(db.String(20), nullable=False)
    is_complete = db.Column(db.Boolean, default=False)
    time_spent = db.Column(db.Integer, default=0)  # seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert game to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'sandstorm_user_id': self.sandstorm_user_id,
            'user_handle': self.user_handle,
            'board_state': json.loads(self.board_state),
            'original_puzzle': json.loads(self.original_puzzle),
            'difficulty': self.difficulty,
            'is_complete': self.is_complete,
            'time_spent': self.time_spent,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

# Sudoku Logic Classes (same as before but more compact)
class SudokuGenerator:
    def __init__(self):
        self.grid = [[0 for _ in range(9)] for _ in range(9)]

    def is_valid_move(self, grid, row, col, num):
        # Check row
        for x in range(9):
            if grid[row][x] == num:
                return False

        # Check column
        for x in range(9):
            if grid[x][col] == num:
                return False

        # Check 3x3 box
        start_row = row - row % 3
        start_col = col - col % 3
        for i in range(3):
            for j in range(3):
                if grid[i + start_row][j + start_col] == num:
                    return False

        return True

    def solve_sudoku(self, grid):
        for i in range(9):
            for j in range(9):
                if grid[i][j] == 0:
                    numbers = list(range(1, 10))
                    random.shuffle(numbers)
                    for num in numbers:
                        if self.is_valid_move(grid, i, j, num):
                            grid[i][j] = num
                            if self.solve_sudoku(grid):
                                return True
                            grid[i][j] = 0
                    return False
        return True

    def generate_complete_board(self):
        self.grid = [[0 for _ in range(9)] for _ in range(9)]

        # Fill diagonal 3x3 boxes first
        for box in range(0, 9, 3):
            self.fill_box(box, box)

        self.solve_sudoku(self.grid)
        return copy.deepcopy(self.grid)

    def fill_box(self, row, col):
        numbers = list(range(1, 10))
        random.shuffle(numbers)
        for i in range(3):
            for j in range(3):
                self.grid[row + i][col + j] = numbers[i * 3 + j]

    def generate_puzzle(self, difficulty='medium'):
        complete_board = self.generate_complete_board()
        puzzle = copy.deepcopy(complete_board)

        cells_to_remove = {
            'easy': 41,     # ~40 filled cells
            'medium': 49,   # ~32 filled cells  
            'hard': 55      # ~26 filled cells
        }

        positions = [(i, j) for i in range(9) for j in range(9)]
        random.shuffle(positions)

        for i in range(cells_to_remove.get(difficulty, 49)):
            if i < len(positions):
                row, col = positions[i]
                puzzle[row][col] = 0

        return puzzle, complete_board

class SudokuValidator:
    @staticmethod
    def is_valid_sudoku(board):
        # Check rows
        for row in board:
            if not SudokuValidator.is_valid_unit([cell for cell in row if cell != 0]):
                return False

        # Check columns
        for col in range(9):
            column = [board[row][col] for row in range(9) if board[row][col] != 0]
            if not SudokuValidator.is_valid_unit(column):
                return False

        # Check 3x3 boxes
        for box_row in range(3):
            for box_col in range(3):
                box = []
                for i in range(3):
                    for j in range(3):
                        cell = board[box_row * 3 + i][box_col * 3 + j]
                        if cell != 0:
                            box.append(cell)
                if not SudokuValidator.is_valid_unit(box):
                    return False

        return True

    @staticmethod
    def is_valid_unit(unit):
        return len(unit) == len(set(unit))

    @staticmethod
    def is_complete(board):
        for row in board:
            for cell in row:
                if cell == 0:
                    return False
        return SudokuValidator.is_valid_sudoku(board)

# Routes with Sandstorm Integration
@app.route('/')
def index():
    """Main page - shows user info for debugging in development"""
    user_id = SandstormUser.get_user_id(request)
    user_handle = SandstormUser.get_preferred_handle(request)
    permissions = SandstormUser.get_permissions(request)

    # Pass user info to template for potential display
    return render_template('index.html', 
                         user_id=user_id, 
                         user_handle=user_handle, 
                         permissions=permissions)

@app.route('/api/user-info', methods=['GET'])
def get_user_info():
    """API endpoint to get current user information"""
    return jsonify({
        'success': True,
        'user_id': SandstormUser.get_user_id(request),
        'user_handle': SandstormUser.get_preferred_handle(request),
        'permissions': SandstormUser.get_permissions(request)
    })

@app.route('/api/new-game', methods=['POST'])
def new_game():
    try:
        data = request.get_json()
        difficulty = data.get('difficulty', 'medium')

        # Get Sandstorm user information
        user_id = SandstormUser.get_user_id(request)
        user_handle = SandstormUser.get_preferred_handle(request)

        # Generate new puzzle
        generator = SudokuGenerator()
        puzzle, solution = generator.generate_puzzle(difficulty)

        # Create game record with Sandstorm user ID
        game = SudokuGame(
            sandstorm_user_id=user_id,
            user_handle=user_handle,
            board_state=json.dumps(puzzle),
            original_puzzle=json.dumps(puzzle),
            difficulty=difficulty
        )

        db.session.add(game)
        db.session.commit()

        return jsonify({
            'success': True,
            'game_id': game.id,
            'puzzle': puzzle,
            'difficulty': difficulty,
            'user_handle': user_handle
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recent-incomplete-game', methods=['GET'])
def get_recent_incomplete_game():
    """Get the most recently modified incomplete game for the current user"""
    try:
        user_id = SandstormUser.get_user_id(request)
        
        # Find the most recent incomplete game
        recent_game = SudokuGame.query.filter_by(
            sandstorm_user_id=user_id, 
            is_complete=False
        ).order_by(SudokuGame.updated_at.desc()).first()
        
        if not recent_game:
            return jsonify({
                'success': True, 
                'has_incomplete_game': False,
                'message': 'No incomplete games found'
            })
        
        return jsonify({
            'success': True,
            'has_incomplete_game': True,
            'game': recent_game.to_dict()
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/game/<int:game_id>', methods=['GET'])
def get_game(game_id):
    try:
        user_id = SandstormUser.get_user_id(request)
        game = SudokuGame.query.filter_by(id=game_id, sandstorm_user_id=user_id).first()

        if not game:
            return jsonify({'success': False, 'error': 'Game not found'}), 404

        return jsonify({
            'success': True,
            'game': game.to_dict()
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/game/<int:game_id>', methods=['PUT'])
def save_game(game_id):
    try:
        data = request.get_json()
        user_id = SandstormUser.get_user_id(request)
        user_handle = SandstormUser.get_preferred_handle(request)

        game = SudokuGame.query.filter_by(id=game_id, sandstorm_user_id=user_id).first()

        if not game:
            return jsonify({'success': False, 'error': 'Game not found'}), 404

        # Update game state
        if 'board_state' in data:
            game.board_state = json.dumps(data['board_state'])

        if 'time_spent' in data:
            game.time_spent = data['time_spent']

        if 'is_complete' in data:
            game.is_complete = data['is_complete']

        # Update user handle in case it changed
        game.user_handle = user_handle
        game.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({'success': True, 'message': 'Game saved successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/games', methods=['GET'])
def get_user_games():
    try:
        user_id = SandstormUser.get_user_id(request)
        games = SudokuGame.query.filter_by(sandstorm_user_id=user_id).order_by(SudokuGame.updated_at.desc()).all()

        games_data = []
        for game in games:
            games_data.append({
                'id': game.id,
                'difficulty': game.difficulty,
                'is_complete': game.is_complete,
                'time_spent': game.time_spent,
                'user_handle': game.user_handle,
                'created_at': game.created_at.isoformat(),
                'updated_at': game.updated_at.isoformat()
            })

        return jsonify({'success': True, 'games': games_data})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/validate', methods=['POST'])
def validate_board():
    try:
        data = request.get_json()
        board = data.get('board')

        if not board:
            return jsonify({'success': False, 'error': 'Board data required'}), 400

        is_valid = SudokuValidator.is_valid_sudoku(board)
        is_complete = SudokuValidator.is_complete(board)

        # Find conflicts for user feedback
        conflicts = []
        if not is_valid:
            conflicts = find_conflicts(board)

        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'is_complete': is_complete,
            'conflicts': conflicts
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def find_conflicts(board):
    """Find conflicting cells on the Sudoku board"""
    conflicts = []

    # Check rows for conflicts
    for row in range(9):
        seen = {}
        for col in range(9):
            if board[row][col] != 0:
                if board[row][col] in seen:
                    conflicts.extend([{'row': row, 'col': col}, seen[board[row][col]]])
                else:
                    seen[board[row][col]] = {'row': row, 'col': col}

    # Check columns for conflicts  
    for col in range(9):
        seen = {}
        for row in range(9):
            if board[row][col] != 0:
                if board[row][col] in seen:
                    conflicts.extend([{'row': row, 'col': col}, seen[board[row][col]]])
                else:
                    seen[board[row][col]] = {'row': row, 'col': col}

    # Check 3x3 boxes for conflicts
    for box_row in range(3):
        for box_col in range(3):
            seen = {}
            for i in range(3):
                for j in range(3):
                    row = box_row * 3 + i
                    col = box_col * 3 + j
                    if board[row][col] != 0:
                        if board[row][col] in seen:
                            conflicts.extend([{'row': row, 'col': col}, seen[board[row][col]]])
                        else:
                            seen[board[row][col]] = {'row': row, 'col': col}

    return conflicts

# Debug route for Sandstorm development
@app.route('/debug/headers')
def debug_headers():
    """Debug endpoint to see all HTTP headers (useful during development)"""
    headers_dict = dict(request.headers)
    return jsonify({
        'headers': headers_dict,
        'sandstorm_user_id': SandstormUser.get_user_id(request),
        'preferred_handle': SandstormUser.get_preferred_handle(request),
        'permissions': SandstormUser.get_permissions(request)
    })

if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            print("Database initialized successfully!")
            print(f"Database location: {app.config['SQLALCHEMY_DATABASE_URI']}")
        except Exception as e:
            print(f"Database initialization error: {e}")

    # Run the application
    print("Starting Sandstorm Sudoku Flask Application...")
    print("This app is designed to run in Sandstorm.io containers")
    print("Visit http://127.0.0.1:5000 for development testing")
