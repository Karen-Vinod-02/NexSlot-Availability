// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

// Form validation
(function () {
    'use strict'
    const forms = document.querySelectorAll('.needs-validation')
    Array.from(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault()
                event.stopPropagation()
            }
            form.classList.add('was-validated')
        }, false)
    })
})();

// Confirm delete actions
document.querySelectorAll('[data-confirm]').forEach(function(element) {
    element.addEventListener('click', function(e) {
        if (!confirm(this.dataset.confirm)) {
            e.preventDefault();
        }
    });
});

// Dynamic form handling for booking type
const bookingTypeRadios = document.querySelectorAll('input[name="is_guest_lecture"]');
if (bookingTypeRadios.length > 0) {
    bookingTypeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            const isGuest = this.value === 'true';
            document.querySelectorAll('.regular-class-fields').forEach(el => {
                el.style.display = isGuest ? 'none' : 'block';
            });
            document.querySelectorAll('.guest-lecture-fields').forEach(el => {
                el.style.display = isGuest ? 'block' : 'none';
            });
        });
    });
}

// Star rating for feedback
function initStarRating() {
    const ratingInputs = document.querySelectorAll('input[type="range"][name="rating"]');
    ratingInputs.forEach(input => {
        const display = document.createElement('div');
        display.className = 'star-rating-display';
        display.innerHTML = '★'.repeat(input.value) + '☆'.repeat(5 - input.value);
        input.parentNode.insertBefore(display, input.nextSibling);
        
        input.addEventListener('input', function() {
            display.innerHTML = '★'.repeat(this.value) + '☆'.repeat(5 - this.value);
        });
    });
}

document.addEventListener('DOMContentLoaded', initStarRating);

// Table search functionality
function initTableSearch() {
    const searchInput = document.getElementById('tableSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const filter = this.value.toUpperCase();
            const table = document.querySelector('.table');
            const tr = table.getElementsByTagName('tr');
            
            for (let i = 1; i < tr.length; i++) {
                let found = false;
                const td = tr[i].getElementsByTagName('td');
                for (let j = 0; j < td.length; j++) {
                    if (td[j].innerHTML.toUpperCase().indexOf(filter) > -1) {
                        found = true;
                        break;
                    }
                }
                tr[i].style.display = found ? '' : 'none';
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', initTableSearch);