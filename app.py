"""
Library Management System - Main Application
A complete web-based library management system built with Flask and SQLite.
"""

from flask import (Flask, render_template, request, redirect, url_for,
                   flash, session, jsonify)
from database import get_db, init_db
from datetime import datetime, timedelta
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)


# ─── Authentication Decorator ────────────────────────────────────────────────

def login_required(f):
    """Decorator to require login for admin/librarian routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def member_login_required(f):
    """Decorator to require member login for member routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'member_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('member_login'))
        return f(*args, **kwargs)
    return decorated_function


# ─── Authentication Routes ───────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, password)
        ).fetchone()
        db.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.route('/')
@login_required
def dashboard():
    db = get_db()

    # Stats
    total_books = db.execute('SELECT COUNT(*) FROM books').fetchone()[0]
    total_members = db.execute('SELECT COUNT(*) FROM members').fetchone()[0]
    active_borrows = db.execute(
        "SELECT COUNT(*) FROM borrowings WHERE status IN ('Borrowed', 'Overdue')"
    ).fetchone()[0]
    overdue_count = db.execute(
        "SELECT COUNT(*) FROM borrowings WHERE status = 'Overdue'"
    ).fetchone()[0]
    total_available = db.execute('SELECT SUM(available_copies) FROM books').fetchone()[0] or 0

    # Recent borrowings
    recent_borrowings = db.execute('''
        SELECT b.*, bk.title as book_title, bk.author as book_author, bk.cover_color,
               m.first_name, m.last_name, m.member_id as mem_id, m.avatar_color
        FROM borrowings b
        JOIN books bk ON b.book_id = bk.id
        JOIN members m ON b.member_id = m.id
        ORDER BY b.created_at DESC
        LIMIT 8
    ''').fetchall()

    # Category distribution
    categories = db.execute('''
        SELECT c.name, c.icon, COUNT(bk.id) as book_count
        FROM categories c
        LEFT JOIN books bk ON c.id = bk.category_id
        GROUP BY c.id
        ORDER BY book_count DESC
    ''').fetchall()

    # Popular books
    popular_books = db.execute('''
        SELECT bk.*, c.name as category_name,
               COUNT(br.id) as borrow_count
        FROM books bk
        LEFT JOIN categories c ON bk.category_id = c.id
        LEFT JOIN borrowings br ON bk.id = br.book_id
        GROUP BY bk.id
        ORDER BY borrow_count DESC
        LIMIT 5
    ''').fetchall()

    db.close()

    return render_template('dashboard.html',
                           total_books=total_books,
                           total_members=total_members,
                           active_borrows=active_borrows,
                           overdue_count=overdue_count,
                           total_available=total_available,
                           recent_borrowings=recent_borrowings,
                           categories=categories,
                           popular_books=popular_books)


# ─── Books Management ────────────────────────────────────────────────────────

@app.route('/books')
@login_required
def books():
    db = get_db()
    search = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()

    query = '''
        SELECT bk.*, c.name as category_name
        FROM books bk
        LEFT JOIN categories c ON bk.category_id = c.id
        WHERE 1=1
    '''
    params = []

    if search:
        query += ' AND (bk.title LIKE ? OR bk.author LIKE ? OR bk.isbn LIKE ?)'
        params.extend([f'%{search}%'] * 3)

    if category_filter:
        query += ' AND c.name = ?'
        params.append(category_filter)

    query += ' ORDER BY bk.created_at DESC'
    all_books = db.execute(query, params).fetchall()

    categories = db.execute('SELECT * FROM categories ORDER BY name').fetchall()
    db.close()

    return render_template('books.html', books=all_books, categories=categories,
                           search=search, category_filter=category_filter)


@app.route('/books/add', methods=['POST'])
@login_required
def add_book():
    db = get_db()
    colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316',
              '#22c55e', '#14b8a6', '#06b6d4', '#3b82f6', '#a855f7']
    import random

    try:
        db.execute('''
            INSERT INTO books (isbn, title, author, category_id, publisher,
                             year_published, total_copies, available_copies, description, cover_color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form['isbn'],
            request.form['title'],
            request.form['author'],
            request.form.get('category_id') or None,
            request.form.get('publisher', ''),
            request.form.get('year_published') or None,
            int(request.form.get('total_copies', 1)),
            int(request.form.get('total_copies', 1)),
            request.form.get('description', ''),
            random.choice(colors)
        ))
        db.commit()
        flash('Book added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding book: {str(e)}', 'error')
    finally:
        db.close()

    return redirect(url_for('books'))


@app.route('/books/edit/<int:book_id>', methods=['POST'])
@login_required
def edit_book(book_id):
    db = get_db()
    try:
        old_book = db.execute('SELECT total_copies, available_copies FROM books WHERE id = ?', (book_id,)).fetchone()
        new_total = int(request.form.get('total_copies', 1))
        diff = new_total - old_book['total_copies']
        new_available = max(0, old_book['available_copies'] + diff)

        db.execute('''
            UPDATE books SET isbn=?, title=?, author=?, category_id=?, publisher=?,
                           year_published=?, total_copies=?, available_copies=?, description=?
            WHERE id=?
        ''', (
            request.form['isbn'],
            request.form['title'],
            request.form['author'],
            request.form.get('category_id') or None,
            request.form.get('publisher', ''),
            request.form.get('year_published') or None,
            new_total,
            new_available,
            request.form.get('description', ''),
            book_id
        ))
        db.commit()
        flash('Book updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating book: {str(e)}', 'error')
    finally:
        db.close()

    return redirect(url_for('books'))


@app.route('/books/delete/<int:book_id>', methods=['POST'])
@login_required
def delete_book(book_id):
    db = get_db()
    try:
        active = db.execute(
            "SELECT COUNT(*) FROM borrowings WHERE book_id = ? AND status IN ('Borrowed', 'Overdue')",
            (book_id,)
        ).fetchone()[0]
        if active > 0:
            flash('Cannot delete book with active borrowings.', 'error')
        else:
            db.execute('DELETE FROM borrowings WHERE book_id = ?', (book_id,))
            db.execute('DELETE FROM books WHERE id = ?', (book_id,))
            db.commit()
            flash('Book deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting book: {str(e)}', 'error')
    finally:
        db.close()

    return redirect(url_for('books'))


# ─── Members Management ──────────────────────────────────────────────────────

@app.route('/members')
@login_required
def members():
    db = get_db()
    search = request.args.get('search', '').strip()

    query = '''
        SELECT m.*, COUNT(CASE WHEN br.status IN ('Borrowed', 'Overdue') THEN 1 END) as active_borrows
        FROM members m
        LEFT JOIN borrowings br ON m.id = br.member_id
        WHERE 1=1
    '''
    params = []

    if search:
        query += ' AND (m.first_name LIKE ? OR m.last_name LIKE ? OR m.email LIKE ? OR m.member_id LIKE ?)'
        params.extend([f'%{search}%'] * 4)

    query += ' GROUP BY m.id ORDER BY m.created_at DESC'
    all_members = db.execute(query, params).fetchall()
    db.close()

    return render_template('members.html', members=all_members, search=search)


@app.route('/members/add', methods=['POST'])
@login_required
def add_member():
    db = get_db()
    colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316',
              '#22c55e', '#14b8a6', '#06b6d4', '#3b82f6', '#a855f7']
    import random

    try:
        # Generate member ID
        last = db.execute('SELECT member_id FROM members ORDER BY id DESC LIMIT 1').fetchone()
        if last:
            num = int(last['member_id'].split('-')[1]) + 1
        else:
            num = 1
        member_id = f'LIB-{num:03d}'

        db.execute('''
            INSERT INTO members (member_id, first_name, last_name, email, phone,
                               address, membership_type, avatar_color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            member_id,
            request.form['first_name'],
            request.form['last_name'],
            request.form['email'],
            request.form.get('phone', ''),
            request.form.get('address', ''),
            request.form.get('membership_type', 'Standard'),
            random.choice(colors)
        ))
        db.commit()
        flash(f'Member {member_id} added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding member: {str(e)}', 'error')
    finally:
        db.close()

    return redirect(url_for('members'))


@app.route('/members/edit/<int:member_id>', methods=['POST'])
@login_required
def edit_member(member_id):
    db = get_db()
    try:
        db.execute('''
            UPDATE members SET first_name=?, last_name=?, email=?, phone=?,
                             address=?, membership_type=?, status=?
            WHERE id=?
        ''', (
            request.form['first_name'],
            request.form['last_name'],
            request.form['email'],
            request.form.get('phone', ''),
            request.form.get('address', ''),
            request.form.get('membership_type', 'Standard'),
            request.form.get('status', 'Active'),
            member_id
        ))
        db.commit()
        flash('Member updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating member: {str(e)}', 'error')
    finally:
        db.close()

    return redirect(url_for('members'))


@app.route('/members/delete/<int:member_id>', methods=['POST'])
@login_required
def delete_member(member_id):
    db = get_db()
    try:
        active = db.execute(
            "SELECT COUNT(*) FROM borrowings WHERE member_id = ? AND status IN ('Borrowed', 'Overdue')",
            (member_id,)
        ).fetchone()[0]
        if active > 0:
            flash('Cannot delete member with active borrowings.', 'error')
        else:
            db.execute('DELETE FROM borrowings WHERE member_id = ?', (member_id,))
            db.execute('DELETE FROM members WHERE id = ?', (member_id,))
            db.commit()
            flash('Member deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting member: {str(e)}', 'error')
    finally:
        db.close()

    return redirect(url_for('members'))


# ─── Borrowings Management ───────────────────────────────────────────────────

@app.route('/borrowings')
@login_required
def borrowings():
    db = get_db()
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = '''
        SELECT br.*, bk.title as book_title, bk.author as book_author, bk.cover_color,
               m.first_name, m.last_name, m.member_id as mem_id, m.avatar_color
        FROM borrowings br
        JOIN books bk ON br.book_id = bk.id
        JOIN members m ON br.member_id = m.id
        WHERE 1=1
    '''
    params = []

    if search:
        query += ' AND (bk.title LIKE ? OR m.first_name LIKE ? OR m.last_name LIKE ? OR m.member_id LIKE ?)'
        params.extend([f'%{search}%'] * 4)

    if status_filter:
        query += ' AND br.status = ?'
        params.append(status_filter)

    query += ' ORDER BY br.created_at DESC'
    all_borrowings = db.execute(query, params).fetchall()

    available_books = db.execute(
        'SELECT * FROM books WHERE available_copies > 0 ORDER BY title'
    ).fetchall()
    active_members = db.execute(
        "SELECT * FROM members WHERE status = 'Active' ORDER BY first_name"
    ).fetchall()

    db.close()

    return render_template('borrowings.html', borrowings=all_borrowings,
                           available_books=available_books, active_members=active_members,
                           search=search, status_filter=status_filter)


@app.route('/borrowings/add', methods=['POST'])
@login_required
def add_borrowing():
    db = get_db()
    try:
        book_id = int(request.form['book_id'])
        member_id = int(request.form['member_id'])
        borrow_date = request.form.get('borrow_date', datetime.now().strftime('%Y-%m-%d'))
        duration = int(request.form.get('duration', 14))
        due_date = (datetime.strptime(borrow_date, '%Y-%m-%d') + timedelta(days=duration)).strftime('%Y-%m-%d')

        # Check availability
        book = db.execute('SELECT available_copies FROM books WHERE id = ?', (book_id,)).fetchone()
        if not book or book['available_copies'] <= 0:
            flash('This book is not available for borrowing.', 'error')
            return redirect(url_for('borrowings'))

        db.execute('''
            INSERT INTO borrowings (book_id, member_id, borrow_date, due_date, status)
            VALUES (?, ?, ?, ?, 'Borrowed')
        ''', (book_id, member_id, borrow_date, due_date))

        db.execute(
            'UPDATE books SET available_copies = available_copies - 1 WHERE id = ?',
            (book_id,)
        )

        db.commit()
        flash('Book borrowed successfully!', 'success')
    except Exception as e:
        flash(f'Error creating borrowing: {str(e)}', 'error')
    finally:
        db.close()

    return redirect(url_for('borrowings'))


@app.route('/borrowings/return/<int:borrowing_id>', methods=['POST'])
@login_required
def return_book(borrowing_id):
    db = get_db()
    try:
        borrowing = db.execute('SELECT * FROM borrowings WHERE id = ?', (borrowing_id,)).fetchone()
        if not borrowing:
            flash('Borrowing record not found.', 'error')
            return redirect(url_for('borrowings'))

        return_date = datetime.now().strftime('%Y-%m-%d')
        due_date = datetime.strptime(borrowing['due_date'], '%Y-%m-%d')
        today = datetime.now()

        # Calculate fine
        fine = 0.0
        if today.date() > due_date.date():
            overdue_days = (today.date() - due_date.date()).days
            fine = overdue_days * 1.0  # RM 1.00 per day

        db.execute('''
            UPDATE borrowings SET return_date = ?, status = 'Returned', fine_amount = ?
            WHERE id = ?
        ''', (return_date, fine, borrowing_id))

        db.execute(
            'UPDATE books SET available_copies = available_copies + 1 WHERE id = ?',
            (borrowing['book_id'],)
        )

        db.commit()
        if fine > 0:
            flash(f'Book returned with fine of RM {fine:.2f} for overdue.', 'warning')
        else:
            flash('Book returned successfully!', 'success')
    except Exception as e:
        flash(f'Error returning book: {str(e)}', 'error')
    finally:
        db.close()

    return redirect(url_for('borrowings'))


# ─── API Endpoints ───────────────────────────────────────────────────────────

@app.route('/api/book/<int:book_id>')
@login_required
def api_get_book(book_id):
    db = get_db()
    book = db.execute('''
        SELECT bk.*, c.name as category_name
        FROM books bk
        LEFT JOIN categories c ON bk.category_id = c.id
        WHERE bk.id = ?
    ''', (book_id,)).fetchone()
    db.close()

    if book:
        return jsonify(dict(book))
    return jsonify({'error': 'Book not found'}), 404


@app.route('/api/member/<int:member_id>')
@login_required
def api_get_member(member_id):
    db = get_db()
    member = db.execute('SELECT * FROM members WHERE id = ?', (member_id,)).fetchone()
    db.close()

    if member:
        return jsonify(dict(member))
    return jsonify({'error': 'Member not found'}), 404


@app.route('/api/stats')
@login_required
def api_stats():
    db = get_db()
    stats = {
        'total_books': db.execute('SELECT COUNT(*) FROM books').fetchone()[0],
        'total_members': db.execute('SELECT COUNT(*) FROM members').fetchone()[0],
        'active_borrows': db.execute(
            "SELECT COUNT(*) FROM borrowings WHERE status IN ('Borrowed', 'Overdue')"
        ).fetchone()[0],
        'overdue': db.execute(
            "SELECT COUNT(*) FROM borrowings WHERE status = 'Overdue'"
        ).fetchone()[0],
    }
    db.close()
    return jsonify(stats)


# ─── Member Portal Routes ────────────────────────────────────────────────────

@app.route('/member/signup', methods=['GET', 'POST'])
def member_signup():
    if 'member_id' in session:
        return redirect(url_for('member_dashboard'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Validation
        if not all([first_name, last_name, username, email, password]):
            flash('Please fill in all required fields.', 'error')
            return render_template('member_signup.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('member_signup.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('member_signup.html')

        db = get_db()
        try:
            # Check for existing username or email
            existing = db.execute(
                'SELECT id FROM members WHERE username = ? OR email = ?',
                (username, email)
            ).fetchone()
            if existing:
                flash('Username or email already exists.', 'error')
                return render_template('member_signup.html')

            # Generate member ID
            import random
            colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316',
                      '#22c55e', '#14b8a6', '#06b6d4', '#3b82f6', '#a855f7']
            last = db.execute('SELECT member_id FROM members ORDER BY id DESC LIMIT 1').fetchone()
            if last:
                num = int(last['member_id'].split('-')[1]) + 1
            else:
                num = 1
            member_id_str = f'LIB-{num:03d}'

            db.execute('''
                INSERT INTO members (member_id, username, password, first_name, last_name,
                                   email, phone, address, membership_type, avatar_color)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Standard', ?)
            ''', (member_id_str, username, password, first_name, last_name,
                  email, phone, address, random.choice(colors)))
            db.commit()

            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('member_login'))
        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'error')
        finally:
            db.close()

    return render_template('member_signup.html')


@app.route('/member/login', methods=['GET', 'POST'])
def member_login():
    if 'member_id' in session:
        return redirect(url_for('member_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        db = get_db()
        member = db.execute(
            'SELECT * FROM members WHERE username = ? AND password = ?',
            (username, password)
        ).fetchone()
        db.close()

        if member:
            if member['status'] != 'Active':
                flash('Your account is inactive. Please contact the library.', 'error')
                return render_template('member_login.html')

            session['member_id'] = member['id']
            session['member_username'] = member['username']
            session['member_name'] = f"{member['first_name']} {member['last_name']}"
            session['member_avatar_color'] = member['avatar_color']
            session['member_member_id'] = member['member_id']
            flash(f"Welcome back, {member['first_name']}!", 'success')
            return redirect(url_for('member_dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('member_login.html')


@app.route('/member/logout')
def member_logout():
    # Clear only member session keys
    for key in list(session.keys()):
        if key.startswith('member_'):
            session.pop(key)
    flash('You have been logged out.', 'info')
    return redirect(url_for('member_login'))


@app.route('/member/dashboard')
@member_login_required
def member_dashboard():
    db = get_db()
    mid = session['member_id']

    # Member stats
    active_borrows = db.execute(
        "SELECT COUNT(*) FROM borrowings WHERE member_id = ? AND status IN ('Borrowed', 'Overdue')",
        (mid,)
    ).fetchone()[0]
    overdue_count = db.execute(
        "SELECT COUNT(*) FROM borrowings WHERE member_id = ? AND status = 'Overdue'",
        (mid,)
    ).fetchone()[0]
    total_borrowed = db.execute(
        'SELECT COUNT(*) FROM borrowings WHERE member_id = ?', (mid,)
    ).fetchone()[0]
    total_fines = db.execute(
        'SELECT COALESCE(SUM(fine_amount), 0) FROM borrowings WHERE member_id = ?', (mid,)
    ).fetchone()[0]

    # Currently borrowed books
    current_books = db.execute('''
        SELECT br.*, bk.title as book_title, bk.author as book_author, bk.cover_color,
               c.name as category_name
        FROM borrowings br
        JOIN books bk ON br.book_id = bk.id
        LEFT JOIN categories c ON bk.category_id = c.id
        WHERE br.member_id = ? AND br.status IN ('Borrowed', 'Overdue')
        ORDER BY br.due_date ASC
    ''', (mid,)).fetchall()

    db.close()

    return render_template('member_dashboard.html',
                           active_borrows=active_borrows,
                           overdue_count=overdue_count,
                           total_borrowed=total_borrowed,
                           total_fines=total_fines,
                           current_books=current_books)


@app.route('/member/books')
@member_login_required
def member_books():
    db = get_db()
    search = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()

    query = '''
        SELECT bk.*, c.name as category_name
        FROM books bk
        LEFT JOIN categories c ON bk.category_id = c.id
        WHERE 1=1
    '''
    params = []

    if search:
        query += ' AND (bk.title LIKE ? OR bk.author LIKE ? OR bk.isbn LIKE ?)'
        params.extend([f'%{search}%'] * 3)

    if category_filter:
        query += ' AND c.name = ?'
        params.append(category_filter)

    query += ' ORDER BY bk.title ASC'
    all_books = db.execute(query, params).fetchall()
    categories = db.execute('SELECT * FROM categories ORDER BY name').fetchall()
    db.close()

    return render_template('member_books.html', books=all_books, categories=categories,
                           search=search, category_filter=category_filter)


@app.route('/member/borrow/<int:book_id>', methods=['POST'])
@member_login_required
def member_borrow(book_id):
    db = get_db()
    mid = session['member_id']
    try:
        # Check availability
        book = db.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
        if not book:
            flash('Book not found.', 'error')
            return redirect(url_for('member_books'))

        if book['available_copies'] <= 0:
            flash('This book is currently not available.', 'error')
            return redirect(url_for('member_books'))

        # Check if member already has this book borrowed
        existing = db.execute(
            "SELECT id FROM borrowings WHERE book_id = ? AND member_id = ? AND status IN ('Borrowed', 'Overdue')",
            (book_id, mid)
        ).fetchone()
        if existing:
            flash('You already have this book borrowed.', 'warning')
            return redirect(url_for('member_books'))

        borrow_date = datetime.now().strftime('%Y-%m-%d')
        due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')

        db.execute('''
            INSERT INTO borrowings (book_id, member_id, borrow_date, due_date, status)
            VALUES (?, ?, ?, ?, 'Borrowed')
        ''', (book_id, mid, borrow_date, due_date))

        db.execute(
            'UPDATE books SET available_copies = available_copies - 1 WHERE id = ?',
            (book_id,)
        )
        db.commit()
        flash(f'Successfully borrowed "{book["title"]}"! Due on {due_date}.', 'success')
    except Exception as e:
        flash(f'Error borrowing book: {str(e)}', 'error')
    finally:
        db.close()

    return redirect(url_for('member_books'))


@app.route('/member/return/<int:borrowing_id>', methods=['POST'])
@member_login_required
def member_return(borrowing_id):
    db = get_db()
    mid = session['member_id']
    try:
        borrowing = db.execute(
            'SELECT * FROM borrowings WHERE id = ? AND member_id = ?',
            (borrowing_id, mid)
        ).fetchone()
        if not borrowing:
            flash('Borrowing record not found.', 'error')
            return redirect(url_for('member_history'))

        return_date = datetime.now().strftime('%Y-%m-%d')
        due_date = datetime.strptime(borrowing['due_date'], '%Y-%m-%d')
        today = datetime.now()

        # Calculate fine
        fine = 0.0
        if today.date() > due_date.date():
            overdue_days = (today.date() - due_date.date()).days
            fine = overdue_days * 1.0

        db.execute('''
            UPDATE borrowings SET return_date = ?, status = 'Returned', fine_amount = ?
            WHERE id = ?
        ''', (return_date, fine, borrowing_id))

        db.execute(
            'UPDATE books SET available_copies = available_copies + 1 WHERE id = ?',
            (borrowing['book_id'],)
        )
        db.commit()
        if fine > 0:
            flash(f'Book returned with fine of RM {fine:.2f} for overdue.', 'warning')
        else:
            flash('Book returned successfully!', 'success')
    except Exception as e:
        flash(f'Error returning book: {str(e)}', 'error')
    finally:
        db.close()

    return redirect(url_for('member_history'))


@app.route('/member/history')
@member_login_required
def member_history():
    db = get_db()
    mid = session['member_id']
    status_filter = request.args.get('status', '').strip()

    query = '''
        SELECT br.*, bk.title as book_title, bk.author as book_author, bk.cover_color,
               c.name as category_name
        FROM borrowings br
        JOIN books bk ON br.book_id = bk.id
        LEFT JOIN categories c ON bk.category_id = c.id
        WHERE br.member_id = ?
    '''
    params = [mid]

    if status_filter:
        query += ' AND br.status = ?'
        params.append(status_filter)

    query += ' ORDER BY br.created_at DESC'
    history = db.execute(query, params).fetchall()
    db.close()

    return render_template('member_history.html', borrowings=history,
                           status_filter=status_filter)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)
