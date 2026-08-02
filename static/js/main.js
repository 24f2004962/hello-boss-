document.addEventListener('DOMContentLoaded', function () {

    // fade out alerts
    var flashes = document.querySelectorAll('.flash-zone .alert');
    flashes.forEach(function (el) {
        setTimeout(function () {
            el.style.transition = 'opacity .4s';
            el.style.opacity = '0';
            setTimeout(function () { el.remove(); }, 400);
        }, 4000);
    });

    // delete prompt
    document.querySelectorAll('form[data-confirm]').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            var msg = form.getAttribute('data-confirm') || 'Are you sure?';
            if (!window.confirm(msg)) {
                e.preventDefault();
            }
        });
    });

    // slots status bars
    document.querySelectorAll('.slots-fill').forEach(function (el) {
        var pct = parseInt(el.getAttribute('data-pct') || '100', 10);
        el.style.width = pct + '%';
        if (pct < 20) el.classList.add('low');
        else if (pct < 50) el.classList.add('mid');
    });

    // Underline title on trek card hover
    document.querySelectorAll('.trek-card').forEach(function (card) {
        var title = card.querySelector('h3');
        card.addEventListener('mouseenter', function () {
            if (title) title.style.textDecoration = 'underline';
        });
        card.addEventListener('mouseleave', function () {
            if (title) title.style.textDecoration = '';
        });
    });

    // Clear search filters
    var clearBtn = document.getElementById('clear-filters');
    if (clearBtn) {
        clearBtn.addEventListener('click', function () {
            var form = clearBtn.closest('form');
            if (!form) return;
            form.querySelectorAll('input[type="text"], input[type="search"]').forEach(function (i) { i.value = ''; });
            form.querySelectorAll('select').forEach(function (s) { s.selectedIndex = 0; });
            form.submit();
        });
    }

    // toggle note field
    var noteToggle = document.getElementById('toggle-note');
    var noteArea = document.getElementById('note-area');
    if (noteToggle && noteArea) {
        noteToggle.addEventListener('click', function () {
            if (noteArea.style.display === 'none' || noteArea.style.display === '') {
                noteArea.style.display = 'block';
                noteToggle.textContent = 'Hide note';
            } else {
                noteArea.style.display = 'none';
                noteToggle.textContent = 'Add a note (optional)';
            }
        });
    }

    // form validation
    document.querySelectorAll('form.validate-form').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            var ok = true;
            form.querySelectorAll('[required]').forEach(function (field) {
                if (!field.value.trim()) {
                    field.style.borderColor = '#ef4444';
                    ok = false;
                } else {
                    field.style.borderColor = '';
                }
            });
            if (!ok) {
                e.preventDefault();
                var err = form.querySelector('.js-error');
                if (err) err.textContent = 'Please fill in all required fields.';
            }
        });
    });

    // report charts data
    var maxEl = document.querySelector('[data-max]');
    if (maxEl) {
        var max = parseInt(maxEl.getAttribute('data-max') || '1', 10) || 1;
        document.querySelectorAll('[data-val]').forEach(function (el) {
            var val = parseInt(el.getAttribute('data-val') || '0', 10);
            el.style.width = Math.round((val / max) * 100) + '%';
        });
    }

});
