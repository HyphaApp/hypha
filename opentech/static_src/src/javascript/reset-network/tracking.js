'use strict';

/**
 * Check whether an tracking cookie has been dropped. If it has then do nothing
 * or init as appropraite. If it hasn't then display the acceptance notice then
 * do nothing or init as appropriate.
 */

var TRACKING = {

  paq: window._paq || [],
  cookieName: 'tracking',

  init: function() {
    var $doc = $(document);

    // Does the tracking cookie exist? If tracking is permitted init tracking
    if (TRACKING.isCookieSet()) {
      if (TRACKING.getCookieValue()) {
        TRACKING.embedTrackingCode();
      }
      setTimeout(function() { // timeout to ensure carousel init is ready for the trigger
        $doc.trigger('cookie-notice-hidden');
      });
      return;
    }

    // Display cookie acceptance notice and await descision
    setTimeout(function() { // timeout to ensure cookie notice is ready for the trigger
      $doc.trigger('cookie-notice-displayed');
    });
    $doc.bind('cookie-notice-dismissed', function(e, trackingPermitted) {
      TRACKING.setCookie(trackingPermitted);
      if (trackingPermitted) {
        TRACKING.embedTrackingCode();
      }
      setTimeout(function() { // timeout to ensure carousel init is ready for the trigger
        $doc.trigger('cookie-notice-hidden');
      });
    });
  },

  setCookie: function(value) {
    var expires = new Date();
    var value = value || false;
    var name = 'cookieName=' + TRACKING.cookieName;

    expires.setFullYear(expires.getFullYear() + 1); // set expirary for one year
    document.cookie = name + '=' + value + '; expires=' + expires.toUTCString() + ';path=/';
  },

  isCookieSet: function() {
    if (document.cookie.split(';').filter(function(item) {
      return item.trim().indexOf('cookieName=' + TRACKING.cookieName) === 0;
    }).length) {
      return true;
    }
    return false;
  },

  getCookieValue: function() {
    if (document.cookie.split(';').filter(function(item) {
      return item.indexOf('cookieName=' + TRACKING.cookieName + '=true') >= 0
    }).length) {
      return true;
    }
    return false;
  },

  embedTrackingCode: function() {
    TRACKING.paq.push(['trackPageView']);
    TRACKING.paq.push(['enableLinkTracking']);

    // @TODO populate $MATOMO_URL & $IDSITE

    // var u="//{$MATOMO_URL}/";
    // TRACKING.paq.push(['setTrackerUrl', u+'matomo.php']);
    // TRACKING.paq.push(['setSiteId', {$IDSITE}]);

    // var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
    // g.type='text/javascript'; g.async=true; g.defer=true; g.src=u+'piwik.js'; s.parentNode.insertBefore(g,s);
  },

};

(function($) {
  $(document).ready(function() {
    TRACKING.init();
  });
})(jQuery);
