class SudokuFlaskGame {
    constructor() {
        this.board = Array(9).fill().map(() => Array(9).fill(0));
        this.originalBoard = Array(9).fill().map(() => Array(9).fill(0));
        this.selectedCell = null;
        this.difficulty = 'easy';
        this.timer = 0;
        this.timerInterval = null;
        this.isComplete = false;
        this.currentGameId = null;
        this.baseURL = ''; // Assuming same origin
        this.userHandle = 'Player';

        this.init();
    }

    async init() {
        await this.loadUserInfo();
        this.bindEvents();
        this.showDifficultySelection();
        this.loadSavedGames();
    }

    async loadUserInfo() {
         try {
            const response = await fetch('/api/user-info');
            const data = await response.json();
            if (data.success) {
                this.userHandle = data.user_handle;
                    document.getElementById('user-handle').textContent = this.userHandle;
                    document.getElementById('user-info').style.display = 'block';
                }
            } catch (error) {
                console.log('User info not available:', error);
            }
        }

    bindEvents() {
        // Difficulty selection
        document.querySelectorAll('.difficulty-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.difficulty = e.target.closest('.difficulty-btn').dataset.difficulty;
                this.startNewGame();
            });
        });

        // Control buttons
        document.getElementById('new-game-btn').addEventListener('click', () => {
            this.showDifficultySelection();
        });

        document.getElementById('validate-btn').addEventListener('click', () => {
            this.validateBoard();
        });

        document.getElementById('save-btn').addEventListener('click', () => {
            this.saveGame();
        });

        document.getElementById('hint-btn').addEventListener('click', () => {
            this.showHint();
        });

        // Number pad
        document.querySelectorAll('.number-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const number = parseInt(e.target.dataset.number) || 0;
                this.inputNumber(number);
            });
        });

        // Modal buttons
        document.getElementById('play-again-btn').addEventListener('click', () => {
            this.hideModal();
            this.showDifficultySelection();
        });

        document.getElementById('close-modal-btn').addEventListener('click', () => {
            this.hideModal();
        });

        // Keyboard input
        document.addEventListener('keydown', (e) => {
            if (this.selectedCell) {
                if (e.key >= '1' && e.key <= '9') {
                    this.inputNumber(parseInt(e.key));
                } else if (e.key === 'Delete' || e.key === 'Backspace' || e.key === '0') {
                    this.inputNumber(0);
                } else if (e.key === 'Escape') {
                    this.selectedCell = null;
                    this.updateBoard();
                }
            }
        });
    }

    async startNewGame() {
        try {
            const response = await fetch('/api/new-game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ difficulty: this.difficulty })
            });

            const data = await response.json();
            if (data.success) {
                this.currentGameId = data.game_id;
                this.board = data.puzzle;
                this.originalBoard = JSON.parse(JSON.stringify(data.puzzle));
                this.difficulty = data.difficulty;
                this.timer = 0;
                this.isComplete = false;
                this.selectedCell = null;

                this.showGameBoard();
                this.updateBoard();
                this.updateDisplay();
                this.startTimer();
                this.loadSavedGames();
            } else {
                console.error('Failed to create new game:', data.error);
                alert('Failed to create new game. Please try again.');
            }
        } catch (error) {
            console.error('Error starting new game:', error);
            alert('Error connecting to server. Please try again.');
        }
    }

    async loadGame(gameId) {
        try {
            const response = await fetch(`/api/game/${gameId}`);
            const data = await response.json();

            if (data.success) {
                const game = data.game;
                this.currentGameId = game.id;
                this.board = game.board_state;
                this.originalBoard = game.original_puzzle;
                this.difficulty = game.difficulty;
                this.timer = game.time_spent;
                this.isComplete = game.is_complete;
                this.selectedCell = null;

                this.showGameBoard();
                this.updateBoard();
                this.updateDisplay();

                if (!this.isComplete) {
                    this.startTimer();
                }
            } else {
                console.error('Failed to load game:', data.error);
                alert('Failed to load game.');
            }
        } catch (error) {
            console.error('Error loading game:', error);
            alert('Error loading game.');
        }
    }

    async saveGame() {
        if (!this.currentGameId) return;

        try {
            const response = await fetch(`/api/game/${this.currentGameId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    board_state: this.board,
                    time_spent: this.timer,
                    is_complete: this.isComplete
                })
            });

            const data = await response.json();
            if (data.success) {
                this.showMessage('Game saved successfully!', 'success');
                this.loadSavedGames();
            } else {
                console.error('Failed to save game:', data.error);
                this.showMessage('Failed to save game.', 'error');
            }
        } catch (error) {
            console.error('Error saving game:', error);
            this.showMessage('Error saving game.', 'error');
        }
    }

    async validateBoard() {
        try {
            const response = await fetch('/api/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ board: this.board })
            });

            const data = await response.json();
            if (data.success) {
                if (data.is_complete) {
                    this.isComplete = true;
                    this.stopTimer();
                    this.saveGame();
                    this.showCompletionModal();
                } else if (data.is_valid) {
                    this.showMessage('Board is valid so far!', 'success');
                } else {
                    this.showMessage('There are conflicts in the board.', 'warning');
                    this.highlightConflicts(data.conflicts);
                }
            }
        } catch (error) {
            console.error('Error validating board:', error);
            this.showMessage('Error validating board.', 'error');
        }
    }

    async loadSavedGames() {
        try {
            const response = await fetch('/api/games');
            const data = await response.json();

            if (data.success) {
                this.displaySavedGames(data.games);
            }
        } catch (error) {
            console.error('Error loading saved games:', error);
        }
    }

    displaySavedGames(games) {
        const container = document.getElementById('saved-games-list');
        container.innerHTML = '';

        if (games.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #666;">No saved games</p>';
            return;
        }

        games.forEach(game => {
            const gameItem = document.createElement('div');
            gameItem.className = 'saved-game-item';
            gameItem.innerHTML = `
                <div class="saved-game-info">
                    <span class="saved-game-difficulty">${game.difficulty}</span>
                    <span class="saved-game-time">${this.formatTime(game.time_spent)}</span>
                </div>
                <div class="saved-game-date">${new Date(game.updated_at).toLocaleDateString()}</div>
                ${game.is_complete ? '<div style="color: #10b981; font-size: 0.8rem;">✓ Completed</div>' : ''}
            `;

            gameItem.addEventListener('click', () => {
                this.loadGame(game.id);
            });

            container.appendChild(gameItem);
        });
    }

    showGameBoard() {
        document.getElementById('difficulty-selection').style.display = 'none';
        document.getElementById('game-board-screen').style.display = 'block';
    }

    showDifficultySelection() {
        document.getElementById('difficulty-selection').style.display = 'block';
        document.getElementById('game-board-screen').style.display = 'none';
        this.stopTimer();
    }

    createBoard() {
        const board = document.getElementById('sudoku-board');
        board.innerHTML = '';

        for (let row = 0; row < 9; row++) {
            for (let col = 0; col < 9; col++) {
                const cell = document.createElement('div');
                cell.className = 'sudoku-cell';
                cell.dataset.row = row;
                cell.dataset.col = col;

                cell.addEventListener('click', () => {
                    if (!this.originalBoard[row][col]) {
                        this.selectCell(row, col);
                    }
                });

                board.appendChild(cell);
            }
        }
    }

    selectCell(row, col) {
        this.selectedCell = { row, col };
        this.updateBoard();
    }

    inputNumber(number) {
        if (!this.selectedCell) return;

        const { row, col } = this.selectedCell;
        if (this.originalBoard[row][col]) return; // Can't modify original numbers

        this.board[row][col] = number;
        this.updateBoard();

        // Auto-save after each move
        if (this.currentGameId) {
            this.saveGame();
        }
    }

    updateBoard() {
        if (!document.getElementById('sudoku-board').hasChildNodes()) {
            this.createBoard();
        }

        const cells = document.querySelectorAll('.sudoku-cell');
        cells.forEach(cell => {
            const row = parseInt(cell.dataset.row);
            const col = parseInt(cell.dataset.col);
            const value = this.board[row][col];

            cell.textContent = value || '';
            cell.className = 'sudoku-cell';

            if (this.originalBoard[row][col]) {
                cell.classList.add('original');
            }

            if (this.selectedCell && this.selectedCell.row === row && this.selectedCell.col === col) {
                cell.classList.add('selected');
            }
        });
    }

    highlightConflicts(conflicts) {
        setTimeout(() => {
            conflicts.forEach(conflict => {
                const cell = document.querySelector(`[data-row="${conflict.row}"][data-col="${conflict.col}"]`);
                if (cell) {
                    cell.classList.add('conflict');
                }
            });
        }, 100);

        // Remove conflict highlighting after 3 seconds
        setTimeout(() => {
            document.querySelectorAll('.conflict').forEach(cell => {
                cell.classList.remove('conflict');
            });
        }, 3000);
    }

    startTimer() {
        this.stopTimer();
        this.timerInterval = setInterval(() => {
            this.timer++;
            this.updateTimerDisplay();
        }, 1000);
    }

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    updateTimerDisplay() {
        const display = document.getElementById('timer-display');
        display.textContent = this.formatTime(this.timer);
    }

    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    updateDisplay() {
        document.getElementById('current-difficulty').textContent = 
            this.difficulty.charAt(0).toUpperCase() + this.difficulty.slice(1);
        this.updateTimerDisplay();
    }

    showHint() {
        if (!this.selectedCell) {
            this.showMessage('Please select a cell first.', 'info');
            return;
        }

        const { row, col } = this.selectedCell;
        if (this.originalBoard[row][col]) {
            this.showMessage('Cannot give hint for original numbers.', 'info');
            return;
        }

        // Simple hint: find valid numbers for the selected cell
        const validNumbers = [];
        for (let num = 1; num <= 9; num++) {
            if (this.isValidMove(row, col, num)) {
                validNumbers.push(num);
            }
        }

        if (validNumbers.length === 1) {
            this.showMessage(`Hint: The only valid number is ${validNumbers[0]}`, 'info');
        } else if (validNumbers.length > 0) {
            this.showMessage(`Hint: Valid numbers are ${validNumbers.join(', ')}`, 'info');
        } else {
            this.showMessage('No valid numbers for this cell.', 'warning');
        }
    }

    isValidMove(row, col, num) {
        // Check row
        for (let c = 0; c < 9; c++) {
            if (c !== col && this.board[row][c] === num) return false;
        }

        // Check column
        for (let r = 0; r < 9; r++) {
            if (r !== row && this.board[r][col] === num) return false;
        }

        // Check 3x3 box
        const boxRow = Math.floor(row / 3) * 3;
        const boxCol = Math.floor(col / 3) * 3;
        for (let r = boxRow; r < boxRow + 3; r++) {
            for (let c = boxCol; c < boxCol + 3; c++) {
                if ((r !== row || c !== col) && this.board[r][c] === num) return false;
            }
        }

        return true;
    }

    showCompletionModal() {
        document.getElementById('final-time').textContent = this.formatTime(this.timer);
        document.getElementById('final-difficulty').textContent = 
            this.difficulty.charAt(0).toUpperCase() + this.difficulty.slice(1);
        document.getElementById('success-modal').style.display = 'flex';
    }

    hideModal() {
        document.getElementById('success-modal').style.display = 'none';
    }

    showMessage(message, type = 'info') {
        // Create a simple toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 24px;
            background-color: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#06b6d4'};
            color: white;
            border-radius: 8px;
            z-index: 1001;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Add CSS for toast animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); }
        to { transform: translateX(0); }
    }

    @keyframes slideOut {
        from { transform: translateX(0); }
        to { transform: translateX(100%); }
    }
`;
document.head.appendChild(style);

// Initialize game when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SudokuFlaskGame();
});