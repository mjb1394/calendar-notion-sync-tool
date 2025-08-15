// NurseSync Pro - Enhanced JavaScript
class NurseSyncApp {
    constructor() {
        this.init();
        this.setupEventListeners();
        this.startPeriodicUpdates();
    }

    init() {
        this.updateLastSyncTime();
        this.initializeAnimations();
        this.setupLoadingOverlay();
        this.initializeTooltips();
    }

    setupEventListeners() {
        // Form submissions with loading states
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => {
                this.showLoading();
                this.disableFormInputs(form);
            });
        });

        // Button click animations
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.createRippleEffect(e);
            });
        });

        // Auto-hide flash messages
        document.querySelectorAll('.flash').forEach(flash => {
            setTimeout(() => {
                this.fadeOutElement(flash);
            }, 5000);
        });

        // Sidebar mobile toggle
        this.setupMobileNavigation();

        // Real-time sync status updates
        this.setupSyncStatusUpdates();

        // Enhanced form validation
        this.setupFormValidation();
    }

    // Loading States
    showLoading(message = 'Processing...') {
        const overlay = document.getElementById('loading-overlay');
        const text = overlay.querySelector('.loading-text');
        text.textContent = message;
        overlay.classList.add('active');
    }

    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        overlay.classList.remove('active');
    }

    setupLoadingOverlay() {
        // Hide loading on page load
        window.addEventListener('load', () => {
            this.hideLoading();
        });

        // Show loading for navigation
        document.querySelectorAll('a[href]:not([href^="#"])').forEach(link => {
            link.addEventListener('click', (e) => {
                if (!link.target || link.target === '_self') {
                    this.showLoading('Loading page...');
                }
            });
        });
    }

    // Animations
    initializeAnimations() {
        // Intersection Observer for scroll animations
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('.card, .stat-card').forEach(el => {
            observer.observe(el);
        });

        // Stagger animation for dashboard cards
        document.querySelectorAll('.dashboard-grid .stat-card').forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
            card.classList.add('slide-in');
        });
    }

    createRippleEffect(e) {
        const button = e.currentTarget;
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;

        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s ease-out;
            pointer-events: none;
        `;

        button.style.position = 'relative';
        button.style.overflow = 'hidden';
        button.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
    }

    fadeOutElement(element) {
        element.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
        element.style.opacity = '0';
        element.style.transform = 'translateY(-20px)';
        setTimeout(() => element.remove(), 500);
    }

    // Mobile Navigation
    setupMobileNavigation() {
        // Create mobile menu toggle if it doesn't exist
        if (window.innerWidth <= 768 && !document.querySelector('.mobile-menu-toggle')) {
            this.createMobileMenuToggle();
        }

        // Handle window resize
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) {
                document.querySelector('.sidebar')?.classList.remove('open');
            }
        });
    }

    createMobileMenuToggle() {
        const toggle = document.createElement('button');
        toggle.className = 'mobile-menu-toggle';
        toggle.innerHTML = '☰';
        toggle.style.cssText = `
            position: fixed;
            top: 1rem;
            left: 1rem;
            z-index: 1001;
            background: var(--gradient-primary);
            border: none;
            color: white;
            width: 48px;
            height: 48px;
            border-radius: 12px;
            font-size: 1.5rem;
            cursor: pointer;
            box-shadow: var(--shadow-lg);
        `;

        toggle.addEventListener('click', () => {
            document.querySelector('.sidebar').classList.toggle('open');
        });

        document.body.appendChild(toggle);
    }

    // Sync Status Updates
    setupSyncStatusUpdates() {
        this.updateSyncStatus();
        setInterval(() => this.updateSyncStatus(), 30000); // Update every 30 seconds
    }

    updateSyncStatus() {
        // Simulate sync status check
        const statusElement = document.querySelector('.sync-text');
        if (statusElement) {
            const now = new Date();
            const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            statusElement.innerHTML = `Last sync: <span id="last-sync-time">${timeString}</span>`;
        }
    }

    updateLastSyncTime() {
        const syncTimeElement = document.getElementById('last-sync-time');
        if (syncTimeElement) {
            const now = new Date();
            syncTimeElement.textContent = now.toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        }
    }

    // Form Enhancements
    setupFormValidation() {
        document.querySelectorAll('.form-input, .form-select, .form-textarea').forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearFieldError(input));
        });
    }

    validateField(field) {
        const value = field.value.trim();
        const isRequired = field.hasAttribute('required');
        
        if (isRequired && !value) {
            this.showFieldError(field, 'This field is required');
            return false;
        }

        if (field.type === 'email' && value && !this.isValidEmail(value)) {
            this.showFieldError(field, 'Please enter a valid email address');
            return false;
        }

        if (field.type === 'date' && value && new Date(value) < new Date()) {
            this.showFieldError(field, 'Date cannot be in the past');
            return false;
        }

        this.clearFieldError(field);
        return true;
    }

    showFieldError(field, message) {
        this.clearFieldError(field);
        
        const errorElement = document.createElement('div');
        errorElement.className = 'field-error';
        errorElement.textContent = message;
        errorElement.style.cssText = `
            color: var(--medical-red);
            font-size: 0.875rem;
            margin-top: 0.25rem;
            animation: slideInDown 0.3s ease-out;
        `;

        field.style.borderColor = 'var(--medical-red)';
        field.parentNode.appendChild(errorElement);
    }

    clearFieldError(field) {
        const errorElement = field.parentNode.querySelector('.field-error');
        if (errorElement) {
            errorElement.remove();
        }
        field.style.borderColor = '';
    }

    isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    disableFormInputs(form) {
        form.querySelectorAll('input, select, textarea, button').forEach(input => {
            input.disabled = true;
        });
    }

    // Tooltips
    initializeTooltips() {
        document.querySelectorAll('[data-tooltip]').forEach(element => {
            element.addEventListener('mouseenter', (e) => this.showTooltip(e));
            element.addEventListener('mouseleave', () => this.hideTooltip());
        });
    }

    showTooltip(e) {
        const text = e.target.getAttribute('data-tooltip');
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = text;
        tooltip.style.cssText = `
            position: absolute;
            background: var(--surface-bg);
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            font-size: 0.875rem;
            z-index: 1000;
            box-shadow: var(--shadow-lg);
            border: 1px solid var(--border-color);
            pointer-events: none;
            animation: fadeIn 0.2s ease-out;
        `;

        document.body.appendChild(tooltip);

        const rect = e.target.getBoundingClientRect();
        tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
        tooltip.style.top = `${rect.top - tooltip.offsetHeight - 8}px`;

        this.currentTooltip = tooltip;
    }

    hideTooltip() {
        if (this.currentTooltip) {
            this.currentTooltip.remove();
            this.currentTooltip = null;
        }
    }

    // Periodic Updates
    startPeriodicUpdates() {
        // Update time displays every minute
        setInterval(() => {
            this.updateTimeDisplays();
        }, 60000);

        // Check for notifications every 5 minutes
        setInterval(() => {
            this.checkForNotifications();
        }, 300000);
    }

    updateTimeDisplays() {
        document.querySelectorAll('[data-time]').forEach(element => {
            const timestamp = element.getAttribute('data-time');
            element.textContent = this.formatRelativeTime(new Date(timestamp));
        });
    }

    formatRelativeTime(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        return date.toLocaleDateString();
    }

    checkForNotifications() {
        // Simulate checking for new notifications
        // In a real app, this would make an API call
        console.log('Checking for notifications...');
    }

    // Utility Methods
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `flash flash-${type}`;
        notification.innerHTML = `
            <span class="flash-icon">${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
            <span class="flash-text">${message}</span>
            <button class="flash-close" onclick="this.parentElement.remove()">×</button>
        `;

        const container = document.querySelector('.flash-messages') || document.querySelector('.content-wrapper');
        container.insertBefore(notification, container.firstChild);

        setTimeout(() => this.fadeOutElement(notification), 5000);
    }

    // API Helper Methods
    async makeRequest(url, options = {}) {
        this.showLoading();
        
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.hideLoading();
            return data;
        } catch (error) {
            this.hideLoading();
            this.showNotification(`Error: ${error.message}`, 'error');
            throw error;
        }
    }
}

// CSS for ripple effect
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(2);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.nurseSyncApp = new NurseSyncApp();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NurseSyncApp;
}
