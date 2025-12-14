from flask import Flask, render_template, redirect, url_for, request, session
import sqlite3

DB_PATH = "db.sqlite3"

app = Flask(__name__)
app.secret_key = "The quick brown fox jumps over the fence."  # required for sessions

# ---------------- Template loader ----------------
AVAILABLE_TEMPLATES = [
    "tailwind",
    "bootstrap",    
    "bulma",
    "daisy_ui",	
    "foundation",
    "generic",
    "materialize",	
    "metro_ui",
    "milligram",
    "minicss",	
    "papercss",
    "picocss",	
    "purecss",
    "semantic_ui",
    "skeleton",	
    "ui_toolkit"
]

# Set the template module you want to use
TEMPLATE_MODULE = "tailwind"  # change this to any in AVAILABLE_TEMPLATES

# Ensure it is valid
if TEMPLATE_MODULE not in AVAILABLE_TEMPLATES:
    raise ValueError(f"Invalid TEMPLATE_MODULE '{TEMPLATE_MODULE}'. Must be one of {AVAILABLE_TEMPLATES}")

# Function to get template path
def template_path(name):
    """
    Return the path to the template inside the module folder.
    Checks session for a selected theme; falls back to default TEMPLATE_MODULE.
    """
    theme = session.get('theme', TEMPLATE_MODULE)
    return f"{theme}/{name}.html"


@app.route('/set_theme', methods=['POST'])
def set_theme():
    selected_theme = request.form.get('theme')
    if selected_theme in AVAILABLE_TEMPLATES:
        session['theme'] = selected_theme
    return redirect(request.referrer or url_for('index'))


# Make template_path available in Jinja templates
@app.context_processor
def inject_template_path():
    return dict(
        template_path=template_path,
        AVAILABLE_TEMPLATES=AVAILABLE_TEMPLATES
    )

# ---------------- Database helper ----------------

# Get all categories
def get_categories():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM categories ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Get all books
def get_books():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT b.id, b.title, b.hepburn, b.author, b.published_date,
               b.release, b.url, b.summary, b.category_id, c.name AS category_name
        FROM books b
        LEFT JOIN categories c ON b.category_id = c.id
        ORDER BY b.id
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Get a single book by id
def get_book(book_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT b.id, b.title, b.hepburn, b.author, b.published_date,
               b.release, b.url, b.summary,
               b.category_id, c.name AS category_name
        FROM books b
        LEFT JOIN categories c ON b.category_id = c.id
        WHERE b.id = ?
    """, (book_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

# Insert a new book
def insert_book(data):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO books (title, hepburn, author, published_date, release, url, summary, category_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('title'),
        data.get('hepburn'),
        data.get('author'),
        data.get('published_date'),
        data.get('release'),
        data.get('url'),
        data.get('summary'),
        data.get('category_id') or None
    ))
    conn.commit()
    conn.close()

# Update an existing book
def update_book(book_id, data):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        UPDATE books
        SET title=?, hepburn=?, author=?, published_date=?, release=?, url=?, summary=?, category_id=?
        WHERE id=?
    """, (
        data.get('title'),
        data.get('hepburn'),
        data.get('author'),
        data.get('published_date'),
        data.get('release'),
        data.get('url'),
        data.get('summary'),
        data.get('category_id') or None,
        book_id
    ))
    conn.commit()
    conn.close()

# Delete a book
def delete_book(book_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()
    conn.close()


# ---------------- Routes ----------------

# List all books
@app.route('/')
def index():
    books = get_books()
    return render_template(template_path('list'), books=books)

# View a single book
@app.route('/view/<int:book_id>')
def view(book_id):
    book = get_book(book_id)
    return render_template(template_path('view'), book=book)

# Edit a book
@app.route('/edit/<int:book_id>', methods=['GET', 'POST'])
def edit(book_id):
    book = get_book(book_id)
    categories = get_categories()  # Fetch categories for dropdown
    if request.method == 'POST':
        update_book(book_id, request.form)
        return redirect(url_for('index'))
    return render_template(template_path('form'), book=book, categories=categories)

# Add a new book
@app.route('/add', methods=['GET', 'POST'])
def add():
    categories = get_categories()  # Fetch categories for dropdown
    if request.method == 'POST':
        insert_book(request.form)
        return redirect(url_for('index'))
    return render_template(template_path('form'), book=None, categories=categories)


# Delete a book
@app.route('/delete/<int:book_id>')
def delete(book_id):
    delete_book(book_id)
    return redirect(url_for('index'))

# Dummy page
# @app.route('/add', methods=['GET', 'POST'])
# def add():
#    return "Add new book (dummy page)"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
