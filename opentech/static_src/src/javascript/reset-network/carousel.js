/* eslint-env jquery */

(function () {

    'use strict';

    var CAROUSEL = {

        init: function () {
            CAROUSEL.HERO.init();
            CAROUSEL.RESOURCES.init();
        },

        // *********************************************************************
        // ********************* HOMEPAGE HERO CAROUSEL ************************
        // *********************************************************************

        HERO: {

            $carousel: null,
            $imgs: null,
            speedImgChange: 700,
            collapsed: false,

            utils: {

                preloadImg: function (src) {
                    var img = new Image();
                    var dfd = $.Deferred();
                    img.onload = dfd.resolve();
                    img.src = src;
                    return dfd.promise();
                },

                preloadImgs: function ($imgs) {
                    var promises = [];
                    var dfd = $.Deferred();
                    for (let i = 0; i < $imgs.length; i++) {
                        var src = $($imgs[i]).children('img').attr('src');
                        promises.push(CAROUSEL.HERO.utils.preloadImg(src));
                    }
                    $.when.apply($, promises).then(dfd.resolve());
                    return dfd.promise();
                }
            },

            init: function () {
                if (!$('#hero-carousel').length) {
                    return;
                }

                CAROUSEL.HERO.$carousel = $('#hero-carousel');
                CAROUSEL.HERO.$imgs = CAROUSEL.HERO.$carousel.find('.hero-carousel__item');

                if (window.innerWidth <= 768) {
                    CAROUSEL.HERO.$carousel.addClass('is-collapsed');
                }

                var $document = $(document);
                var $firstCarouselItem = CAROUSEL.HERO.$imgs.first();
                var firstImgSrc = $firstCarouselItem.children('.hero-carousel__image').attr('src');
                var positionTimeout = null;
                var dfdMinTimeout = $.Deferred();
                var dfdCookieNotice = $.Deferred();
                var promises = [
                    CAROUSEL.HERO.utils.preloadImgs(CAROUSEL.HERO.$imgs),
                    dfdMinTimeout.promise(),
                    dfdCookieNotice.promise()
                ];

                // Fade up the first image ASAP
                CAROUSEL.HERO.utils.preloadImg(firstImgSrc).then(function () {
                    $firstCarouselItem.addClass('is-displayed');
                });

                // Position the carousel on load (and on screen resize)
                CAROUSEL.HERO.positionCarousel();
                window.addEventListener('resize', function () {
                    clearTimeout(positionTimeout);
                    positionTimeout = setTimeout(function () {
                        if (CAROUSEL.HERO.collapsed) {
                            return; // no need to position the carousel once it's shrunk
                        }
                        CAROUSEL.HERO.positionCarousel();
                    }, 500);
                });

                // Wait for cookie notice dismissal before permitting animations
                $document.bind('cookie-notice-hidden', dfdCookieNotice.resolve);

                // Commence hero animations
                setTimeout(dfdMinTimeout.resolve, 500);
                $.when.apply($, promises).then(function () {
                    CAROUSEL.HERO.collapsed = true;
                    CAROUSEL.HERO.animate();

                    $document.on('scroll', function () {
                        clearInterval(CAROUSEL.HERO.animateInterval);
                        $document.off('scroll');
                        setTimeout(function () {
                            $document.trigger('artifacts-animate');
                        }, 250); // enough time to allow for completion of an in-progress carousel image change
                    });
                });

                // Collapse the carousel when the logo moves to the corners
                $document.bind('artifacts-cornered', function () {
                    CAROUSEL.HERO.animate();
                    CAROUSEL.HERO.$carousel.addClass('is-collapsed');
                });
            },

            positionCarousel: function () {
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
                    'margin-right': offsetR + 'px'
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
            animate: function () {
                clearInterval(CAROUSEL.HERO.animateInterval);
                CAROUSEL.HERO.animateInterval = setInterval(CAROUSEL.HERO.changeImg, CAROUSEL.HERO.speedImgChange);
                CAROUSEL.HERO.changeImg();
            }
        },

        // *********************************************************************
        // *********************** RESOURCES CAROUSEL **************************
        // *********************************************************************

        RESOURCES: {

            $carousel: null,
            $copyItems: null,
            config: {
                arrows: false,
                centerMode: true,
                slidesToShow: 3,
                centerPadding: 0,
                vertical: true,
                verticalSwiping: true
            },

            init: function () {

                CAROUSEL.RESOURCES.$carousel = $('.js-resources-carousel');

                // If there is only 1 item in the carousel just show 1 slide
                // If there are 2 items in the carousel dupe them to create a functional carousel
                var itemsLength = CAROUSEL.RESOURCES.$carousel.children('li').length;
                if (itemsLength < 3) {
                    if (itemsLength === 1) {
                        CAROUSEL.RESOURCES.config.slidesToShow = 1;
                        CAROUSEL.RESOURCES.$carousel.addClass('has-one-item');
                    }
                    else if (itemsLength === 2) {
                        $('.js-resources-carousel li:nth-child(1)').clone().appendTo('.js-resources-carousel');
                        $('.js-resources-carousel li:nth-child(2)').clone().appendTo('.js-resources-carousel');

                        $('.js-resources-copy li:nth-child(1)').clone().attr('data-resources-copy', 2).appendTo('.js-resources-copy');
                        $('.js-resources-copy li:nth-child(2)').clone().attr('data-resources-copy', 3).appendTo('.js-resources-copy');
                    }
                }

                CAROUSEL.RESOURCES.$copyItems = $('.js-resources-copy li');

                // Fade in first slide on init
                CAROUSEL.RESOURCES.$carousel.on('init', function () {
                    CAROUSEL.RESOURCES.revealSlide(0);
                    CAROUSEL.RESOURCES.revealCopy(0);
                });

                // Fade in current slide
                CAROUSEL.RESOURCES.$carousel.on('afterChange', function (e, slick, currentSlide, nextSlide) {
                    CAROUSEL.RESOURCES.revealSlide(currentSlide);
                    CAROUSEL.RESOURCES.revealCopy(currentSlide);
                });

                // Add mousewheel scroll
                CAROUSEL.RESOURCES.$carousel.on('wheel', CAROUSEL.RESOURCES.onScroll);

                // Init
                CAROUSEL.RESOURCES.$carousel.slick(CAROUSEL.RESOURCES.config);
            },

            revealSlide: function (index) {
                CAROUSEL.RESOURCES.$carousel.find('.resources__carousel-imgs-item').removeClass('is-revealed');
                CAROUSEL.RESOURCES.$carousel.find('[data-slick-index="' + index + '"]').addClass('is-revealed');
            },

            revealCopy: function (index) {
                var $displayCopyItem = CAROUSEL.RESOURCES.$copyItems.filter('[data-resources-copy="' + index + '"]');

                CAROUSEL.RESOURCES.$copyItems.removeClass('is-revealed');
                $displayCopyItem.addClass('is-revealed');
            },

            onScroll: function (e) {
                e.preventDefault();

                if (e.originalEvent.deltaY > 0) {
                    CAROUSEL.RESOURCES.$carousel.slick('slickNext');
                }
                else {
                    CAROUSEL.RESOURCES.$carousel.slick('slickPrev');
                }
            }
        }

    };

    (function ($) {
        $(document).ready(function () {
            CAROUSEL.init();
        });
    })(jQuery);

})();

