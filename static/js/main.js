/**
 * Library Management System - Frontend JavaScript
 * Handles modals, flash messages, search, and UI interactions.
 */

// ── Modal Management ─────────────────────────────────────────────────────────

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Close modal on overlay click
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
        document.body.style.overflow = '';
    }
});

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.active').forEach(modal => {
            modal.classList.remove('active');
        });
        document.body.style.overflow = '';
    }
});


// ── Edit Modals (populate form with existing data) ───────────────────────────

function editBook(bookId) {
    fetch(`/api/book/${bookId}`)
        .then(res => res.json())
        .then(book => {
            const form = document.getElementById('editBookForm');
            form.action = `/books/edit/${bookId}`;
            form.querySelector('[name="isbn"]').value = book.isbn || '';
            form.querySelector('[name="title"]').value = book.title || '';
            form.querySelector('[name="author"]').value = book.author || '';
            form.querySelector('[name="category_id"]').value = book.category_id || '';
            form.querySelector('[name="publisher"]').value = book.publisher || '';
            form.querySelector('[name="year_published"]').value = book.year_published || '';
            form.querySelector('[name="total_copies"]').value = book.total_copies || 1;
            form.querySelector('[name="description"]').value = book.description || '';
            openModal('editBookModal');
        })
        .catch(err => console.error('Error fetching book:', err));
}

function editMember(memberId) {
    fetch(`/api/member/${memberId}`)
        .then(res => res.json())
        .then(member => {
            const form = document.getElementById('editMemberForm');
            form.action = `/members/edit/${memberId}`;
            form.querySelector('[name="first_name"]').value = member.first_name || '';
            form.querySelector('[name="last_name"]').value = member.last_name || '';
            form.querySelector('[name="email"]').value = member.email || '';
            form.querySelector('[name="phone"]').value = member.phone || '';
            form.querySelector('[name="address"]').value = member.address || '';
            form.querySelector('[name="membership_type"]').value = member.membership_type || 'Standard';
            form.querySelector('[name="status"]').value = member.status || 'Active';
            openModal('editMemberModal');
        })
        .catch(err => console.error('Error fetching member:', err));
}

function confirmDelete(type, id, name) {
    const modal = document.getElementById('deleteConfirmModal');
    const form = document.getElementById('deleteForm');
    const nameEl = document.getElementById('deleteItemName');
    
    form.action = `/${type}/delete/${id}`;
    nameEl.textContent = name;
    openModal('deleteConfirmModal');
}


// ── Flash Messages ───────────────────────────────────────────────────────────

function dismissFlash(el) {
    el.parentElement.style.animation = 'flashSlideOut 0.3s ease forwards';
    setTimeout(() => el.parentElement.remove(), 300);
}

// Auto-dismiss flash messages
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach((msg, index) => {
        setTimeout(() => {
            if (msg.parentElement) {
                msg.style.animation = 'flashSlideOut 0.3s ease forwards';
                setTimeout(() => msg.remove(), 300);
            }
        }, 4000 + (index * 500));
    });
});


// ── Search Functionality ─────────────────────────────────────────────────────

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Live search for page search boxes
document.addEventListener('DOMContentLoaded', function() {
    const searchInputs = document.querySelectorAll('.search-box input[data-search]');
    searchInputs.forEach(input => {
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                const url = new URL(window.location.href);
                url.searchParams.set('search', this.value);
                window.location.href = url.toString();
            }
        });
    });

    // Category filter
    const categoryFilter = document.getElementById('categoryFilter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', function() {
            const url = new URL(window.location.href);
            if (this.value) {
                url.searchParams.set('category', this.value);
            } else {
                url.searchParams.delete('category');
            }
            url.searchParams.delete('search');
            window.location.href = url.toString();
        });
    }

    // Status filter
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            const url = new URL(window.location.href);
            if (this.value) {
                url.searchParams.set('status', this.value);
            } else {
                url.searchParams.delete('status');
            }
            url.searchParams.delete('search');
            window.location.href = url.toString();
        });
    }
});


// ── Mobile Sidebar ───────────────────────────────────────────────────────────

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
    if (overlay) {
        overlay.classList.toggle('active');
    }
}


// ── Animate elements on page load ────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function() {
    // Staggered animation for cards
    const cards = document.querySelectorAll('.stat-card, .book-card, .member-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(15px)';
        setTimeout(() => {
            card.style.transition = 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 50 + (index * 60));
    });

    // Counter animation for stat values
    const statValues = document.querySelectorAll('.stat-value[data-count]');
    statValues.forEach(el => {
        const target = parseInt(el.getAttribute('data-count'));
        let current = 0;
        const increment = Math.ceil(target / 30);
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            el.textContent = current.toLocaleString();
        }, 30);
    });
});


// ── Availability bar colors ──────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.availability-bar .fill').forEach(bar => {
        const pct = parseFloat(bar.style.width) || 0;
        if (pct > 60) {
            bar.style.background = 'var(--gradient-success)';
        } else if (pct > 30) {
            bar.style.background = 'var(--gradient-warm)';
        } else {
            bar.style.background = 'var(--gradient-danger)';
        }
    });
});
