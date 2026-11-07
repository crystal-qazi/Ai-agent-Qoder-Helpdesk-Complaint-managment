// Hospital Complaint Tracking System - Main JavaScript

(function() {
    'use strict';

    // Auto-dismiss flash messages after 5 seconds
    document.addEventListener('DOMContentLoaded', function() {
        const flashMessages = document.querySelectorAll('[class*="animate-slide-in"]');
        flashMessages.forEach(function(msg) {
            setTimeout(function() {
                msg.style.transition = 'opacity 0.5s, transform 0.5s';
                msg.style.opacity = '0';
                msg.style.transform = 'translateX(100%)';
                setTimeout(function() { msg.remove(); }, 500);
            }, 5000);
        });
    });

    // Color picker sync
    const colorPickers = document.querySelectorAll('input[type="color"]');
    colorPickers.forEach(function(picker) {
        const hexInput = picker.closest('.flex')?.querySelector('input[type="text"]');
        if (hexInput) {
            picker.addEventListener('input', function() {
                hexInput.value = this.value;
            });
            hexInput.addEventListener('input', function() {
                if (/^#[0-9A-Fa-f]{6}$/.test(this.value)) {
                    picker.value = this.value;
                }
            });
        }
    });

    // Confirm dialogs for destructive actions
    document.querySelectorAll('[data-confirm]').forEach(function(el) {
        el.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // Mobile sidebar toggle
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebarOverlay = document.getElementById('sidebar-overlay');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('-translate-x-full');
            if (sidebarOverlay) sidebarOverlay.classList.toggle('hidden');
        });
    }

    const sidebarClose = document.getElementById('sidebar-close');
    if (sidebarClose && sidebar) {
        sidebarClose.addEventListener('click', function() {
            sidebar.classList.add('-translate-x-full');
            if (sidebarOverlay) sidebarOverlay.classList.add('hidden');
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            sidebar.classList.add('-translate-x-full');
            this.classList.add('hidden');
        });
    }

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar && !sidebar.classList.contains('-translate-x-full')) {
            sidebar.classList.add('-translate-x-full');
            if (sidebarOverlay) sidebarOverlay.classList.add('hidden');
        }
    });

    // Date/time format helper
    window.formatDate = function(dateStr, format) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        if (format === 'relative') {
            const now = new Date();
            const diff = Math.floor((now - date) / 1000);
            if (diff < 60) return 'just now';
            if (diff < 3600) return Math.floor(diff / 60) + ' min ago';
            if (diff < 86400) return Math.floor(diff / 3600) + ' hours ago';
            if (diff < 604800) return Math.floor(diff / 86400) + ' days ago';
            return date.toLocaleDateString();
        }
        return date.toLocaleString();
    };

    // Search debounce
    window.debounce = function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    };

    // Filter form auto-submit on change
    document.querySelectorAll('.auto-submit').forEach(function(select) {
        select.addEventListener('change', function() {
            const form = this.closest('form');
            if (form) form.submit();
        });
    });

})();