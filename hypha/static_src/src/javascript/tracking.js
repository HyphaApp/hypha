/**
 * @file
 * A JavaScript file for analytic tracking.
 */

var idSite = window.matomo.siteid;
var matomoTrackingApiUrl = 'https://' + window.matomo.url + '/matomo.php';

var _paq = window._paq || [];
_paq.push(['setTrackerUrl', matomoTrackingApiUrl]);
_paq.push(['setSiteId', idSite]);
_paq.push(['trackPageView']);
_paq.push(['enableLinkTracking']);
