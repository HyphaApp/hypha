/* eslint-env jquery */

(function () {

    'use strict';

    // *************************************************************************
    // ***************************** COOKIE NOTICE *****************************
    // *************************************************************************

    var COOKIES = {

        $html: $('html'),
        $doc: $(document),
        $notice: null,

        init: function () {
            COOKIES.$notice = $('#cookie-notice');
            COOKIES.$doc.bind('cookie-notice-displayed', COOKIES.showNotice);
        },

        showNotice: function () {
            COOKIES.$notice.removeClass('is-hidden--before');
            COOKIES.$html.addClass('has-overflow-hidden');
            COOKIES.$notice.find('button').on('click', function () {
                var trackingPermitted = $(this).attr('data-tracking') === 'true' ? true : false;
                COOKIES.hideNotice(trackingPermitted);
            });
        },

        hideNotice: function (trackingPermitted) {
            COOKIES.$notice.addClass('is-hidden--after');
            COOKIES.$html.removeClass('has-overflow-hidden');
            COOKIES.$doc.trigger('cookie-notice-dismissed', trackingPermitted);
        }
    };

    // *************************************************************************
    // ******************************* TRACKING ********************************
    // *************************************************************************

    /**
     * Check whether an tracking cookie has been dropped. If it has then do nothing
     * or init as appropraite. If it hasn't then display the acceptance notice then
     * do nothing or init as appropriate.
     */

    var TRACKING = {

        $doc: $(document),
        cookieName: 'acceptCookie',

        init: function () {

            // Does the tracking cookie exist? If tracking is permitted init tracking
            if (TRACKING.isCookieSet()) {
                if (TRACKING.getCookieValue()) {
                    TRACKING.embedTrackingCode();
                }
                setTimeout(function () { // timeout to ensure carousel init is ready for the trigger
                    TRACKING.$doc.trigger('cookie-notice-hidden');
                });
                return;
            }

            // Display cookie acceptance notice and await descision
            setTimeout(function () { // timeout to ensure cookie notice is ready for the trigger
                TRACKING.$doc.trigger('cookie-notice-displayed');
            });
            TRACKING.$doc.bind('cookie-notice-dismissed', function (e, trackingPermitted) {
                TRACKING.setCookie(trackingPermitted);
                if (trackingPermitted) {
                    TRACKING.embedTrackingCode();
                }
                setTimeout(function () { // timeout to ensure carousel init is ready for the trigger
                    TRACKING.$doc.trigger('cookie-notice-hidden');
                });
            });
        },

        setCookie: function (value) {
            var val = value || false;
            var cookie = TRACKING.cookieName + '=' + val.toString() + ';path=/';
            if (window.location.protocol === 'https:') {
                cookie += ';secure';
            }
            document.cookie = cookie;
        },

        isCookieSet: function () {
            if (document.cookie.split(';').filter(function (item) {
                return item.indexOf(TRACKING.cookieName) >= 0;
            }).length) {
                return true;
            }
            return false;
        },

        getCookieValue: function () {
            if (document.cookie.split(';').filter(function (item) {
                return item.indexOf(TRACKING.cookieName + '=true') >= 0;
            }).length) {
                return true;
            }
            return false;
        },

        embedTrackingCode: function () {
            if (!window.matomo || !window.matomo.url || !window.matomo.siteid) {
                return;
            }

            var url = 'https://' + window.matomo.url + '.matomo.cloud/matomo.php';
            var siteid = window.matomo.siteid;
            var src = '//cdn.matomo.cloud/' + window.matomo.url + '.matomo.cloud/matomo.js';

            var d = document;
            var g = d.createElement('script');
            var s = d.getElementsByTagName('script')[0];
            g.type = 'text/javascript';
            g.async = true;
            g.defer = true;
            g.src = src;
            s.parentNode.insertBefore(g, s);

            g.onload = g.onreadystatechange = function () {
                if (!this.readyState || this.readyState === 'complete') {
                    window.Matomo.getAsyncTracker().setTrackerUrl(url);
                    window.Matomo.getAsyncTracker().setSiteId(siteid);
                    window.Matomo.getAsyncTracker().enableLinkTracking();
                    window.Matomo.getAsyncTracker().trackPageView();
                }
            };
        }
    };

    (function ($) {
        $(document).ready(function () {
            COOKIES.init();
            TRACKING.init();
        });
    })(jQuery);

})();
