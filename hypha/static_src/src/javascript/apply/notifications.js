(function () {

    'use strict';

    // Open/close dropdown when users clicks the bell.
    document.querySelector('.notifications__bell').addEventListener('click', function () {
        document.querySelector('.notifications__content').classList.toggle('hidden');
    });

    // Close the dropdown menu if the user clicks outside of it.
    window.onclick = function (event) {
        if (!event.target.matches('.notifications--dropdown, .notifications--dropdown *')) {
            const dropdown = document.querySelector('.notifications__content');
            if (!dropdown.classList.contains('hidden')) {
                dropdown.classList.add('hidden');
            }
        }
    };


})();
