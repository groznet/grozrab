// Main JavaScript for Грозненский рабочий

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu functionality
    initMobileMenu();
    
    // Search functionality
    initSearch();
    
    // Smooth scrolling for anchor links
    initSmoothScroll();
});

function initMobileMenu() {
    const mobileMenu = document.getElementById('mobileMenu');
    if (!mobileMenu) return;

    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('#mobileMenu') && !event.target.closest('button[onclick*="toggleMobileMenu"]')) {
            mobileMenu.classList.add('hidden');
        }
    });
}

function initSearch() {
    const searchInput = document.querySelector('input[name="q"]');
    if (!searchInput) return;

    // Add focus styles
    searchInput.addEventListener('focus', function() {
        this.parentElement.classList.add('ring-2', 'ring-primary-500');
    });

    searchInput.addEventListener('blur', function() {
        this.parentElement.classList.remove('ring-2', 'ring-primary-500');
    });
}

function initSmoothScroll() {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Share functions
function shareOnTelegram() {
    const url = encodeURIComponent(window.location.href);
    const text = encodeURIComponent(document.title);
    window.open(`https://t.me/share/url?url=${url}&text=${text}`, '_blank');
}

function shareOnWhatsApp() {
    const url = encodeURIComponent(window.location.href);
    const text = encodeURIComponent(document.title);
    window.open(`https://wa.me/?text=${text}%20${url}`, '_blank');
}