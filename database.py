"""
Database module for Library Management System.
Handles SQLite database initialization and helper functions.
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

DATABASE = 'library.db'


def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize the database with tables and sample data."""
    conn = get_db()
    cursor = conn.cursor()

    # Create tables
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'librarian',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            icon TEXT DEFAULT '📚'
        );

        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isbn TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category_id INTEGER,
            publisher TEXT,
            year_published INTEGER,
            total_copies INTEGER DEFAULT 1,
            available_copies INTEGER DEFAULT 1,
            description TEXT,
            cover_color TEXT DEFAULT '#6366f1',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );

        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            address TEXT,
            membership_type TEXT DEFAULT 'Standard',
            status TEXT DEFAULT 'Active',
            join_date DATE DEFAULT CURRENT_DATE,
            avatar_color TEXT DEFAULT '#6366f1',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS borrowings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            member_id INTEGER NOT NULL,
            borrow_date DATE NOT NULL,
            due_date DATE NOT NULL,
            return_date DATE,
            status TEXT DEFAULT 'Borrowed',
            fine_amount REAL DEFAULT 0.0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (book_id) REFERENCES books(id),
            FOREIGN KEY (member_id) REFERENCES members(id)
        );
    ''')

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        _seed_data(cursor)

    conn.commit()
    conn.close()


def _seed_data(cursor):
    """Seed the database with sample data."""

    # Default admin user (password: admin123)
    cursor.execute('''
        INSERT INTO users (username, password, full_name, role)
        VALUES (?, ?, ?, ?)
    ''', ('admin', 'admin123', 'System Administrator', 'admin'))

    # Categories
    categories = [
        ('Fiction', 'Novels, short stories, and literary works', '📖'),
        ('Science', 'Scientific research and discoveries', '🔬'),
        ('Technology', 'Computing, engineering, and tech', '💻'),
        ('History', 'Historical events and civilizations', '🏛️'),
        ('Mathematics', 'Pure and applied mathematics', '📐'),
        ('Philosophy', 'Philosophical works and theories', '🤔'),
        ('Art & Design', 'Visual arts, design, and creativity', '🎨'),
        ('Business', 'Business, economics, and management', '💼'),
        ('Medicine', 'Medical science and healthcare', '⚕️'),
        ('Education', 'Teaching and learning resources', '🎓'),
    ]
    cursor.executemany(
        'INSERT INTO categories (name, description, icon) VALUES (?, ?, ?)',
        categories
    )

    # Books
    colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316',
              '#eab308', '#22c55e', '#14b8a6', '#06b6d4', '#3b82f6']
    books = [
        ('978-0-06-112008-4', 'To Kill a Mockingbird', 'Harper Lee', 1, 'HarperCollins', 1960, 5, 3,
         'A classic novel about racial injustice in the American South.'),
        ('978-0-451-52493-5', '1984', 'George Orwell', 1, 'Signet Classics', 1949, 4, 2,
         'A dystopian novel about totalitarian government surveillance.'),
        ('978-0-7432-7356-5', 'A Brief History of Time', 'Stephen Hawking', 2, 'Bantam Books', 1988, 3, 1,
         'An exploration of cosmology for the general reader.'),
        ('978-0-13-468599-1', 'The C Programming Language', 'Brian Kernighan', 3, 'Prentice Hall', 1978, 3, 2,
         'The definitive guide to C programming.'),
        ('978-0-19-520365-0', 'The Oxford History of Britain', 'Kenneth Morgan', 4, 'Oxford University Press', 1984, 2, 1,
         'A comprehensive history of Britain from Roman times.'),
        ('978-0-07-340481-5', 'Introduction to Algorithms', 'Thomas Cormen', 3, 'MIT Press', 2009, 4, 3,
         'The comprehensive textbook on algorithms.'),
        ('978-0-14-028329-7', 'The Republic', 'Plato', 6, 'Penguin Classics', -380, 2, 2,
         'A Socratic dialogue on justice and the ideal state.'),
        ('978-0-393-91257-8', 'Art Through the Ages', 'Helen Gardner', 7, 'Cengage Learning', 1926, 3, 2,
         'The most widely used art history textbook.'),
        ('978-0-06-093546-7', 'To Kill a Kingdom', 'Alexandra Christo', 1, 'Feiwel & Friends', 2018, 3, 3,
         'A dark fantasy inspired by The Little Mermaid.'),
        ('978-0-13-110362-7', 'The C++ Programming Language', 'Bjarne Stroustrup', 3, 'Addison-Wesley', 1985, 3, 1,
         'The definitive C++ reference by its creator.'),
        ('978-0-07-352332-8', 'Principles of Economics', 'N. Gregory Mankiw', 8, 'Cengage', 1998, 4, 3,
         'A leading textbook in introductory economics.'),
        ('978-0-323-35775-3', 'Gray\'s Anatomy', 'Henry Gray', 9, 'Elsevier', 1858, 2, 1,
         'The classic anatomy reference textbook.'),
        ('978-0-13-468599-2', 'Clean Code', 'Robert C. Martin', 3, 'Prentice Hall', 2008, 5, 4,
         'A handbook of agile software craftsmanship.'),
        ('978-0-06-112009-1', 'Brave New World', 'Aldous Huxley', 1, 'HarperPerennial', 1932, 3, 2,
         'A dystopian novel about a futuristic World State.'),
        ('978-0-262-03384-8', 'Deep Learning', 'Ian Goodfellow', 3, 'MIT Press', 2016, 4, 2,
         'The definitive textbook on deep learning.'),
        ('978-0-07-340481-6', 'Discrete Mathematics', 'Kenneth Rosen', 5, 'McGraw-Hill', 2007, 3, 2,
         'A comprehensive guide to discrete mathematics.'),
        ('978-0-13-235088-4', 'Python Crash Course', 'Eric Matthes', 3, 'No Starch Press', 2015, 6, 5,
         'A hands-on introduction to Python programming.'),
        ('978-0-393-91257-9', 'The Story of Art', 'E.H. Gombrich', 7, 'Phaidon Press', 1950, 2, 1,
         'One of the most famous art books ever written.'),
        ('978-0-19-921613-5', 'Sapiens', 'Yuval Noah Harari', 4, 'Harper', 2011, 5, 3,
         'A brief history of humankind.'),
        ('978-0-07-352332-9', 'The Lean Startup', 'Eric Ries', 8, 'Crown Business', 2011, 3, 2,
         'How entrepreneurs use innovation to build businesses.'),
    ]
    for i, book in enumerate(books):
        cursor.execute('''
            INSERT INTO books (isbn, title, author, category_id, publisher, year_published,
                             total_copies, available_copies, description, cover_color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (*book, colors[i % len(colors)]))

    # Members
    member_colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316',
                     '#22c55e', '#14b8a6', '#06b6d4', '#3b82f6', '#a855f7']
    members = [
        ('LIB-001', 'ahmad.ibrahim', 'member123', 'Ahmad', 'Ibrahim', 'ahmad.ibrahim@email.com', '012-345-6789', '123 Jalan Merdeka, KL', 'Premium'),
        ('LIB-002', 'siti.aminah', 'member123', 'Siti', 'Aminah', 'siti.aminah@email.com', '013-456-7890', '456 Jalan Bunga, Penang', 'Standard'),
        ('LIB-003', 'john.smith', 'member123', 'John', 'Smith', 'john.smith@email.com', '014-567-8901', '789 Baker Street, Johor', 'Premium'),
        ('LIB-004', 'maria.garcia', 'member123', 'Maria', 'Garcia', 'maria.garcia@email.com', '015-678-9012', '321 Oak Avenue, Selangor', 'Standard'),
        ('LIB-005', 'wei.chen', 'member123', 'Wei', 'Chen', 'wei.chen@email.com', '016-789-0123', '654 Maple Road, Melaka', 'Premium'),
        ('LIB-006', 'priya.sharma', 'member123', 'Priya', 'Sharma', 'priya.sharma@email.com', '017-890-1234', '987 Pine Lane, Perak', 'Standard'),
        ('LIB-007', 'ali.hassan', 'member123', 'Ali', 'Hassan', 'ali.hassan@email.com', '018-901-2345', '147 Cedar Blvd, Sabah', 'Standard'),
        ('LIB-008', 'nurul.izzah', 'member123', 'Nurul', 'Izzah', 'nurul.izzah@email.com', '019-012-3456', '258 Elm Street, Sarawak', 'Premium'),
        ('LIB-009', 'david.lee', 'member123', 'David', 'Lee', 'david.lee@email.com', '011-123-4567', '369 Birch Way, Pahang', 'Standard'),
        ('LIB-010', 'fatimah.zahra', 'member123', 'Fatimah', 'Zahra', 'fatimah.zahra@email.com', '012-234-5678', '741 Willow Court, Kedah', 'Premium'),
        ('LIB-011', 'raj.kumar', 'member123', 'Raj', 'Kumar', 'raj.kumar@email.com', '013-345-6789', '852 Spruce Drive, Negeri Sembilan', 'Standard'),
        ('LIB-012', 'tan.meiling', 'member123', 'Tan', 'Mei Ling', 'tan.meiling@email.com', '014-456-7890', '963 Walnut Circle, Terengganu', 'Premium'),
    ]
    for i, member in enumerate(members):
        status = 'Active' if random.random() > 0.15 else 'Inactive'
        cursor.execute('''
            INSERT INTO members (member_id, username, password, first_name, last_name, email, phone, address,
                               membership_type, status, avatar_color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (*member, status, member_colors[i % len(member_colors)]))

    # Borrowings
    today = datetime.now().date()
    borrowings = [
        (1, 1, today - timedelta(days=20), today - timedelta(days=6), today - timedelta(days=5), 'Returned', 0.0),
        (2, 2, today - timedelta(days=15), today - timedelta(days=1), None, 'Borrowed', 0.0),
        (3, 3, today - timedelta(days=25), today - timedelta(days=11), today - timedelta(days=10), 'Returned', 0.0),
        (4, 4, today - timedelta(days=10), today + timedelta(days=4), None, 'Borrowed', 0.0),
        (5, 5, today - timedelta(days=30), today - timedelta(days=16), today - timedelta(days=12), 'Returned', 2.0),
        (6, 1, today - timedelta(days=5), today + timedelta(days=9), None, 'Borrowed', 0.0),
        (10, 6, today - timedelta(days=18), today - timedelta(days=4), None, 'Overdue', 0.0),
        (12, 7, today - timedelta(days=12), today + timedelta(days=2), None, 'Borrowed', 0.0),
        (13, 8, today - timedelta(days=22), today - timedelta(days=8), today - timedelta(days=7), 'Returned', 0.0),
        (15, 9, today - timedelta(days=8), today + timedelta(days=6), None, 'Borrowed', 0.0),
        (17, 10, today - timedelta(days=35), today - timedelta(days=21), None, 'Overdue', 0.0),
        (19, 3, today - timedelta(days=3), today + timedelta(days=11), None, 'Borrowed', 0.0),
        (14, 11, today - timedelta(days=7), today + timedelta(days=7), None, 'Borrowed', 0.0),
        (20, 12, today - timedelta(days=14), today, None, 'Borrowed', 0.0),
    ]
    for b in borrowings:
        cursor.execute('''
            INSERT INTO borrowings (book_id, member_id, borrow_date, due_date, return_date, status, fine_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', b)
