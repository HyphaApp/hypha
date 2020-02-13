'use strict';

var CAROUSEL = {

  init: function() {
    CAROUSEL.HERO.init();
  },

  /*****************************************************************************
  ************************* HOMEPAGE HERO CAROUSEL *****************************
  *****************************************************************************/

  HERO: {

    $carousel: null,
    $imgs: null,
    speedImgChangeQuick: 400,
    speedImgChangeSlow: 2500,
    collapsed: false,

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

    init: function() {
      if (!$('#hero-carousel').length) { return; }

      CAROUSEL.HERO.$carousel = $('#hero-carousel');
      CAROUSEL.HERO.$imgs = CAROUSEL.HERO.$carousel.find('.hero-carousel__item');

      var $document = $(document);
      var $firstCarouselItem = CAROUSEL.HERO.$imgs.first();
      var firstImgSrc = $firstCarouselItem.children('.hero-carousel__image').attr('src');
      var positionTimeout = null;
      var dfdMinTimeout = $.Deferred();
      var dfdCookieNotice = $.Deferred();
      var promises = [
        CAROUSEL.HERO.utils.preloadImgs(CAROUSEL.HERO.$imgs),
        dfdMinTimeout.promise(),
        dfdCookieNotice.promise(),
      ];

      // Fade up the first image ASAP
      CAROUSEL.HERO.utils.preloadImg(firstImgSrc).then(function() {
        $firstCarouselItem.addClass('is-displayed');
      });

      // Position the carousel on load (and on screen resize)
      CAROUSEL.HERO.positionCarousel();
      window.addEventListener('resize', function() {
        clearTimeout(positionTimeout);
        positionTimeout = setTimeout(function() {
          if (CAROUSEL.HERO.collapsed) { return; } // no need to position the carousel once it's shrunk
          CAROUSEL.HERO.positionCarousel();
        }, 500);
      });

      // Wait for cookie notice dismissal before permitting animations
      $document.bind('cookie-notice-hidden', dfdCookieNotice.resolve);

      // Commence hero animations, ensure all images are displayed once before commencing logo animation
      setTimeout(dfdMinTimeout.resolve, 500);
      $.when.apply($, promises).then(function() {
        var duration = CAROUSEL.HERO.$imgs.length * CAROUSEL.HERO.speedImgChangeQuick;

        CAROUSEL.HERO.collapsed = true;
        CAROUSEL.HERO.animate();

        setTimeout(function() {
          $document.trigger('artifacts-animate');
        }, duration);
      });

      // Collapse the carousel when the logo moves to the corners
      $document.bind('artifacts-cornered', function() {
        clearInterval(CAROUSEL.HERO.animateInterval);
        CAROUSEL.HERO.animate(true);
        CAROUSEL.HERO.$carousel.addClass('is-collapsed');
      });
    },

    positionCarousel: function() {
      var $lvlOne = CAROUSEL.HERO.$carousel.find('.hero-carousel__lvl-1');
      var $lvlTwo = CAROUSEL.HERO.$carousel.find('.hero-carousel__lvl-2');
      var $lvlThree = CAROUSEL.HERO.$carousel.find('.hero-carousel__lvl-3');
      var offsetInnerL = $lvlTwo.offset().left;
      var offsetInnerR = CAROUSEL.HERO.$carousel.outerWidth() - ($lvlTwo.outerWidth() + offsetInnerL);
      var offsetOuterL = $lvlOne.offset().left;
      var offsetOuterR = CAROUSEL.HERO.$carousel.outerWidth() - ($lvlOne.outerWidth() + offsetOuterL);
      var offsetL = offsetOuterL - offsetInnerL;
      var offsetR = offsetOuterR - offsetInnerR;

      if (offsetOuterL === 0) {
        offsetL = -250;
        offsetR = -250;
      }

      $lvlThree.css({
        'margin-left': offsetL + 'px',
        'margin-right': offsetR + 'px',
      });

      CAROUSEL.HERO.$carousel.addClass('is-displayed');
    },

    changeImg() {
      CAROUSEL.HERO.animateIndex = CAROUSEL.HERO.animateIndex + 1 >= CAROUSEL.HERO.$imgs.length ? 0 : CAROUSEL.HERO.animateIndex + 1;
      CAROUSEL.HERO.$imgs.removeClass('is-displayed');
      $(CAROUSEL.HERO.$imgs[CAROUSEL.HERO.animateIndex]).addClass('is-displayed');
    },

    animateInterval: null,
    animateIndex: 0,
    animate: function(slow) {
      var speed = slow ? CAROUSEL.HERO.speedImgChangeSlow : CAROUSEL.HERO.speedImgChangeQuick;

      clearInterval(CAROUSEL.HERO.animateInterval)
      CAROUSEL.HERO.animateInterval = setInterval(CAROUSEL.HERO.changeImg, speed);
      CAROUSEL.HERO.changeImg();
    },
  },

};

(function($) {
  $(document).ready(function() {
    CAROUSEL.init();
  });
})(jQuery);
