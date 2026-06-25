# 📚 Library Management System

A modern, full-stack web application designed to efficiently manage library operations, including book inventory, member registrations, and borrowing workflows. Built with Python, Flask, and a beautifully crafted UI.

## ✨ Features

- **🔐 Secure Authentication**: Role-based access control with session management for librarians and members.
- **📊 Interactive Dashboard**: Real-time statistics, recent borrowing activities, popular books, and category breakdowns at a glance.
- **📖 Comprehensive Book Management**: Full CRUD (Create, Read, Update, Delete) operations for books. Track total copies, available copies, and categorize books easily.
- **👥 Member Management**: Register and manage library members, including their contact details, membership tiers (Standard/Premium), and active borrowing status.
- **🔄 Borrowing & Returns Workflow**: Seamlessly issue books to members, process returns, track overdue items, and automatically calculate fines.
- **🎨 Premium UI/UX**: A stunning, responsive dark-themed interface featuring glassmorphism, dynamic gradients, smooth animations, and intuitive navigation.
- **💾 Pre-seeded Database**: Comes with an SQLite database pre-populated with sample data to get you started immediately.

## 🛠️ Tech Stack

- **Backend**: Python 3, Flask, Werkzeug
- **Database**: SQLite
- **Frontend**: HTML5, Vanilla CSS3 (Custom Design System), JavaScript
- **Templating**: Jinja2

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher installed on your system.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Mikaaroni/library-management-system.git
   cd library-management-system
   ```

2. **Set up a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Access the application:**
   Open your web browser and navigate to `http://127.0.0.1:5000`

### 🔑 Default Credentials

- **Admin / Librarian Login:**
  - **Username:** `admin`
  - **Password:** `admin123`

## 📁 Project Structure

```text
library-management-system/
├── app.py              # Main Flask application and routing logic
├── database.py         # Database initialization and sample data seeding
├── requirements.txt    # Python dependencies
├── static/             # Static assets
│   ├── css/
│   │   └── style.css   # Complete custom design system
│   └── js/
│       └── main.js     # Frontend interactions and DOM manipulation
└── templates/          # Jinja2 HTML templates
    ├── base.html       # Base layout with flash messages
    ├── login.html      # Admin/Member login pages
    ├── sidebar.html    # Navigation sidebar component
    ├── dashboard.html  # Analytics dashboard
    ├── books.html      # Book catalog and management
    ├── members.html    # Member directory and management
    └── borrowings.html # Transaction and borrowing records
```

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/yourusername/library-management-system/issues).

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
