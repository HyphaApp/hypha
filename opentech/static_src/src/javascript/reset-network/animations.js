'use strict';

var ANIMATIONS = {

  $doc: null,

  init: function() {

    ANIMATIONS.$doc = $(document);

    // Home page animations require users to start at scroll-top
    if (history && 'scrollRestoration' in history) {
      history.scrollRestoration = 'manual';
    }
    setTimeout(function() {
      ANIMATIONS.$doc.scrollTop(0)
    });

    ANIMATIONS.THEMING.init();
    ANIMATIONS.ARTIFACTS.init();
    ANIMATIONS.NAV.init();
    ANIMATIONS.DRAWER.init();
    ANIMATIONS.COOKIES.init();
    ANIMATIONS.GIFS.init();
  },

  utils:  {

    preloadImg: function(src) {
      var img = new Image();
      var dfd = $.Deferred();

      img.onload = dfd.resolve();
      img.src = src;

      return dfd.promise();
    },

    preloadImgs: function($imgs) {
      var promises = [];
      var dfd = $.Deferred();

      for (let i = 0; i < $imgs.length; i++) {
        var src = $($imgs[i]).children('img').attr('src');
        promises.push(CAROUSEL.HERO.utils.preloadImg(src));
      }
      $.when.apply($, promises).then(dfd.resolve());

      return dfd.promise();
    },
  },

  /*****************************************************************************
  ********************************** THEMING ***********************************
  *****************************************************************************/

  THEMING: {

    themes: [],

    init: function() {
      var timeout = null;

      window.addEventListener('resize', function() {
        clearTimeout(timeout);
        timeout = setTimeout(ANIMATIONS.THEMING.buildThemes, 500);
      });
      ANIMATIONS.$doc.bind('artifacts-cornered', function() {
        setTimeout(ANIMATIONS.THEMING.buildThemes, 750); // Recalculate theming on `artifacts-cornered` as the hero shrinks
      });
      ANIMATIONS.utils.preloadImgs($('img')).then(function() {
        setTimeout(ANIMATIONS.THEMING.buildThemes); // Recalculate theming once all images have loaded
      });
      ANIMATIONS.THEMING.buildThemes();
    },

    // Construct the theming array: a list of all sections flagged with the data-theme attr
    buildThemes: function() {
      var $sections = $('[data-theme]');
      var sections = [];

      for (var i = 0; i < $sections.length; i++) {
        var $section = $($sections[i]);
        sections.push({
          theme: $section.data('theme'),
          scrollY: $section.offset().top,
        });
      }
      ANIMATIONS.THEMING.themes = sections;
    },
  },

  /*****************************************************************************
  ********************************* ARTIFACTS **********************************
  *****************************************************************************/

  ARTIFACTS: {

    $stageHeader: null,
    $artifacts: null,
    forced: false,

    init: function() {
      ANIMATIONS.ARTIFACTS.$stageHeader = $('#stage-header');
      ANIMATIONS.ARTIFACTS.$artifacts = $('.artifact');

      // Trigger the artifacts (logo) animations
      ANIMATIONS.$doc.bind('artifacts-animate', ANIMATIONS.ARTIFACTS.animate);

      // Adjust artifact theming on scroll
      ANIMATIONS.$doc.bind('on-scroll', ANIMATIONS.ARTIFACTS.setTheme);

      // Force theming on drawer open, revert on close
      ANIMATIONS.$doc.bind('drawer-open', function() {
        ANIMATIONS.ARTIFACTS.forced = true;
        ANIMATIONS.ARTIFACTS.setThemeForce();
      });
      ANIMATIONS.$doc.bind('drawer-close', function() {
        ANIMATIONS.ARTIFACTS.forced = false;
        ANIMATIONS.ARTIFACTS.setTheme();
      });

      // Only animate artifact reveal on the homepage
      if (!$('#hero-carousel').length) {
        $('html').addClass('has-no-artifacts-animation');
        ANIMATIONS.ARTIFACTS.$stageHeader.addClass('is-collapsed-artifacts is-cornered-artifacts');
      }

      // Prevent flickering entrance of the logo
      ANIMATIONS.ARTIFACTS.$artifacts.css('opacity', 1);
    },

    setTheme: function() {
      if (ANIMATIONS.ARTIFACTS.forced) { return; }

      for (var i = 0; i < ANIMATIONS.ARTIFACTS.$artifacts.length; i++) {
        var $artifact = $(ANIMATIONS.ARTIFACTS.$artifacts[i]);
        var offsetTop = $artifact.offset().top + $artifact.height()/2;

        for (var j = ANIMATIONS.THEMING.themes.length - 1; j >= 0; j--) {
          var theme = ANIMATIONS.THEMING.themes[j];
          if (offsetTop >= theme.scrollY) {
            $artifact.attr('data-theme', theme.theme);
            break;
          }
        }
      }
    },

    setThemeForce: function() {
      for (var i = 0; i < ANIMATIONS.ARTIFACTS.$artifacts.length; i++) {
        var $artifact = $(ANIMATIONS.ARTIFACTS.$artifacts[i]);

        for (var j = ANIMATIONS.THEMING.themes.length - 1; j >= 0; j--) {
          $artifact.attr('data-theme', 'dark');
        }
      }
    },

    animate: function() {
      ANIMATIONS.ARTIFACTS.$stageHeader.addClass('is-collapsed-artifacts');

      setTimeout(function() {
        ANIMATIONS.ARTIFACTS.$stageHeader.addClass('is-cornered-artifacts');
        ANIMATIONS.$doc.trigger('artifacts-cornered');
        setTimeout(function() {
          ANIMATIONS.ARTIFACTS.setTheme();
          $('html').addClass('is-complete-artifacts-animation');
        }, 750);
      }, 750);
    },
  },

  /*****************************************************************************
  ******************************* NAV THEMING **********************************
  *****************************************************************************/

  NAV: {
    $links: null,

    init: function() {
      ANIMATIONS.NAV.$links = $('#stage-nav .main-nav-link');
      ANIMATIONS.$doc.bind('on-scroll', ANIMATIONS.NAV.setTheme);
      ANIMATIONS.NAV.setTheme();
    },

    // Adjust theming of nav links according to scroll position
    setTheme: function() {
      for (var i = 0; i < ANIMATIONS.NAV.$links.length; i++) {
        var $navItem = $(ANIMATIONS.NAV.$links[i]);
        var offsetTop = $navItem.offset().top + $navItem.height()/2;

        for (var j = ANIMATIONS.THEMING.themes.length - 1; j >= 0; j--) {
          var theme = ANIMATIONS.THEMING.themes[j];
          if (offsetTop >= theme.scrollY) {
            $navItem.attr('data-theme', theme.theme);
            break;
          }
        }
      }
    },
  },

  /*****************************************************************************
  ********************************** DRAWER ************************************
  *****************************************************************************/

  DRAWER: {

    $html: null,
    $drawer: null,
    $links: null,
    $openBtn: null,
    $closeBtn: null,

    init: function() {
      var timeout = null;

      ANIMATIONS.DRAWER.$html = $('html');
      ANIMATIONS.DRAWER.$drawer = ANIMATIONS.DRAWER.$html.find('#stage-drawer');
      ANIMATIONS.DRAWER.$links = ANIMATIONS.DRAWER.$drawer.find('.main-nav-link ');
      ANIMATIONS.DRAWER.$openBtn = ANIMATIONS.DRAWER.$html.find('#open-drawer-btn');
      ANIMATIONS.DRAWER.$closeBtn = ANIMATIONS.DRAWER.$drawer.find('#close-drawer-btn');

      ANIMATIONS.DRAWER.$openBtn.on('click', ANIMATIONS.DRAWER.open);
      ANIMATIONS.DRAWER.$closeBtn.on('click', ANIMATIONS.DRAWER.close);

      window.addEventListener('resize', function() {
        clearTimeout(timeout);
        timeout = setTimeout(ANIMATIONS.DRAWER.close, 500);
      });
    },

    open: function() {
      ANIMATIONS.DRAWER.$html.addClass('is-displayed-drawer has-overflow-hidden');
      ANIMATIONS.DRAWER.$closeBtn.focus();
      ANIMATIONS.DRAWER.$drawer.attr('aria-hidden', false);
      ANIMATIONS.$doc.trigger('drawer-open');

      // Close drawer on keypress escape
      ANIMATIONS.$doc.on('keydown', function(e) {
        if (e.key == 'Escape') {
          ANIMATIONS.DRAWER.close();
        }
      });

      // Loop focus
      ANIMATIONS.DRAWER.$links.last().on('blur', function() {
        ANIMATIONS.DRAWER.$closeBtn.focus();
      });
    },

    close: function() {
      ANIMATIONS.DRAWER.$html.removeClass('has-overflow-hidden is-displayed-drawer');
      ANIMATIONS.$doc.off('keydown');
      ANIMATIONS.DRAWER.$drawer.attr('aria-hidden', true);
      ANIMATIONS.$doc.trigger('drawer-close');
    },
  },

  /*****************************************************************************
  ******************************* COOKIE NOTICE ********************************
  *****************************************************************************/

  COOKIES: {

    $notice: null,

    init: function() {
      ANIMATIONS.COOKIES.$notice = $('#cookie-notice');
      ANIMATIONS.$doc.bind('cookie-notice-displayed', ANIMATIONS.COOKIES.showNotice);
    },

    showNotice: function() {
      ANIMATIONS.COOKIES.$notice.removeClass('is-hidden');
      ANIMATIONS.DRAWER.$html.addClass('has-overflow-hidden');
      ANIMATIONS.COOKIES.$notice.find('button').on('click', function() {
        var trackingPermitted = $(this).attr('data-tracking') === 'true' ? true : false;
        ANIMATIONS.COOKIES.hideNotice(trackingPermitted);
      });
    },

    hideNotice: function(trackingPermitted) {
      ANIMATIONS.COOKIES.$notice.addClass('is-hidden');
      ANIMATIONS.DRAWER.$html.removeClass('has-overflow-hidden');
      ANIMATIONS.$doc.trigger('cookie-notice-dismissed', trackingPermitted);
    },
  },

  /*****************************************************************************
  ************************************ GIFs ************************************
  *****************************************************************************/

  GIFS: {

    $imgs: null,

    init: function() {
      ANIMATIONS.GIFS.$imgs = $('.js-gif-img');
      ANIMATIONS.$doc.bind('on-scroll', ANIMATIONS.GIFS.onScroll);

      // On home page reveal GIFs when animations are complete
      if ($('#hero-carousel').length) {
        ANIMATIONS.$doc.bind('artifacts-cornered', function() {
          setTimeout(ANIMATIONS.GIFS.onScroll, 750);
        });

      // Not home page reveal GIFs on cookie notice dismissal
      } else {
        ANIMATIONS.$doc.bind('cookie-notice-hidden', ANIMATIONS.GIFS.onScroll);
      }
    },

    onScroll: function() {
      var windowTop = window.scrollY + window.innerHeight;

      for (let i = 0; i < ANIMATIONS.GIFS.$imgs.length; i++) {
        var $imgWrapper = $(ANIMATIONS.GIFS.$imgs[i]);

        if ($imgWrapper.hasClass('is-displayed')) {
          continue;
        }

        var scrollTop = $imgWrapper.offset().top;

        if (scrollTop + $imgWrapper.height()/2 <= windowTop) { // Add 50% to ensure a chunk of the GIF displays when animation commences
          var $img = $imgWrapper.children('image');
          var src = $img.attr('src');
          $imgWrapper.addClass('is-displayed');
          $img.attr('src', '').attr('src', src);
        }
      }
    },
  },
};

(function($) {
  $(document).ready(function() {
    ANIMATIONS.init();
  });
})(jQuery);
