(function () {

    'use strict';

    document.querySelector('.simplified__dropbtn').addEventListener('click', function () {
        document.getElementById('downloadDropdown').classList.toggle('simplified__show');
    });

    // Close the dropdown menu if the user clicks outside of it
    window.addEventListener('click', function (event) {
        if (!event.target.matches('.simplified__dropbtn')) {
            var dropdown = document.querySelector('.simplified__dropdown-content');
            if (dropdown.classList.contains('simplified__show')) {
                dropdown.classList.remove('simplified__show');
            }
        }
    });

})();
