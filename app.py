from flask import Flask, request, jsonify, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json
import random
import uuid
from datetime import datetime
import copy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sudoku-game-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/sudoku/sudoku_games.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

# Database Models
class SudokuGame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_session_id = db.Column(db.String(100), nullable=False)
    board_state = db.Column(db.Text, nullable=False)  # JSON string
    original_puzzle = db.Column(db.Text, nullable=False)  # JSON string
    difficulty = db.Column(db.String(20), nullable=False)
    is_complete = db.Column(db.Boolean, default=False)
    time_spent = db.Column(db.Integer, default=0)  # seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Sudoku Logic Classes
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
        # Create a complete valid Sudoku board
        self.grid = [[0 for _ in range(9)] for _ in range(9)]

        # Fill diagonal 3x3 boxes first (they don't affect each other)
        for box in range(0, 9, 3):
            self.fill_box(box, box)

        # Fill remaining cells
        self.solve_sudoku(self.grid)
        return copy.deepcopy(self.grid)

    def fill_box(self, row, col):
        numbers = list(range(1, 10))
        random.shuffle(numbers)
        for i in range(3):
            for j in range(3):
                self.grid[row + i][col + j] = numbers[i * 3 + j]

    def generate_puzzle(self, difficulty='medium'):
        # Generate complete board
        complete_board = self.generate_complete_board()
        puzzle = copy.deepcopy(complete_board)

        # Determine how many cells to remove based on difficulty
        cells_to_remove = {
            'easy': 41,     # ~40 filled cells
            'medium': 49,   # ~32 filled cells  
            'hard': 55      # ~26 filled cells
        }

        # Create list of all positions
        positions = [(i, j) for i in range(9) for j in range(9)]
        random.shuffle(positions)

        # Remove numbers
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

# Helper functions
def get_user_session():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/new-game', methods=['POST'])
def new_game():
    try:
        data = request.get_json()
        difficulty = data.get('difficulty', 'medium')

        # Generate new puzzle
        generator = SudokuGenerator()
        puzzle, solution = generator.generate_puzzle(difficulty)

        # Create game record
        user_session_id = get_user_session()
        game = SudokuGame(
            user_session_id=user_session_id,
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
            'difficulty': difficulty
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/game/<int:game_id>', methods=['GET'])
def get_game(game_id):
    try:
        user_session_id = get_user_session()
        game = SudokuGame.query.filter_by(id=game_id, user_session_id=user_session_id).first()

        if not game:
            return jsonify({'success': False, 'error': 'Game not found'}), 404

        return jsonify({
            'success': True,
            'game': {
                'id': game.id,
                'board_state': json.loads(game.board_state),
                'original_puzzle': json.loads(game.original_puzzle),
                'difficulty': game.difficulty,
                'is_complete': game.is_complete,
                'time_spent': game.time_spent,
                'created_at': game.created_at.isoformat(),
                'updated_at': game.updated_at.isoformat()
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/game/<int:game_id>', methods=['PUT'])
def save_game(game_id):
    try:
        data = request.get_json()
        user_session_id = get_user_session()
        game = SudokuGame.query.filter_by(id=game_id, user_session_id=user_session_id).first()

        if not game:
            return jsonify({'success': False, 'error': 'Game not found'}), 404

        # Update game state
        if 'board_state' in data:
            game.board_state = json.dumps(data['board_state'])

        if 'time_spent' in data:
            game.time_spent = data['time_spent']

        if 'is_complete' in data:
            game.is_complete = data['is_complete']

        game.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'success': True, 'message': 'Game saved successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/games', methods=['GET'])
def get_user_games():
    try:
        user_session_id = get_user_session()
        games = SudokuGame.query.filter_by(user_session_id=user_session_id).order_by(SudokuGame.updated_at.desc()).all()

        games_data = []
        for game in games:
            games_data.append({
                'id': game.id,
                'difficulty': game.difficulty,
                'is_complete': game.is_complete,
                'time_spent': game.time_spent,
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
