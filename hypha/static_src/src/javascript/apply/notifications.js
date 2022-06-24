function notificationToggle() {
    'use strict';
    document.getElementById('notificationDropdown').classList.toggle('show');
}

// Close the dropdown menu if the user clicks outside of it
window.onclick = function (event) {
    'use strict';
    if (!event.target.matches('.dropbtn, .dropbtn *')) {
        var dropdowns = document.getElementsByClassName('dropdown-content');
        var i;
        for (i = 0; i < dropdowns.length; i++) {
            var openDropdown = dropdowns[i];
            if (openDropdown.classList.contains('show')) {
                notificationToggle();
            }
        }
    }
};
