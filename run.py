#!/usr/bin/env python3
"""
Sudoku Flask Application Runner
"""
import os
import sys
from app import app, db

if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")

    # Run the application
    print("Starting Sudoku Flask Application...")
    print("Visit http://127.0.0.1:5000 to play!")
    app.run(debug=True, host='127.0.0.1', port=5000)
