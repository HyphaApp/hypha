import $ from './../globals';

export default function toggleActionsPanel(){
    $('.js-actions-toggle').click(function(e) {
        e.preventDefault();
        this.classList.toggle('is-active');
        this.nextElementSibling.classList.toggle('is-visible');
    });
}

