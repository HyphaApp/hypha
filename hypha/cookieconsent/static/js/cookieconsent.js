(function () {

    'use strict';

    if (typeof window.Cookies !== 'undefined') {
        const cookie_buttons = Array.prototype.slice.call(
            document.querySelectorAll('button[data-consent]')
        );
        const sitedomain = window.location.hostname.split('.').slice(-2);
        const cookiedomain = sitedomain.join('.');
        let cookie_option = [];
        cookie_option['domain'] = cookiedomain;
        cookie_option['expires'] = 365;
        if (window.location.protocol === 'https:') {
            cookie_option['secure'] = true;
        }
        cookie_buttons.forEach(function (button) {
            button.addEventListener('click', function () {
                if (button.getAttribute('data-consent') == 'true') {
                    window.Cookies.set('cookieconsent', 'accept', cookie_option);
                }
                else {
                    window.Cookies.set('cookieconsent', 'decline', cookie_option);
                }
                document.querySelector('.cookieconsent').classList.add('hidden');
            })
        });
    }

})();
