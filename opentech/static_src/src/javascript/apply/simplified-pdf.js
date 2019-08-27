(function () {

    'use strict';

    // remove '&nbsp;' from answers to produce a better pdf
    const allAnswersParagraphs = document.querySelectorAll('.js-simplified-answers p');
    const allAnswersListItems = document.querySelectorAll('.js-simplified-answers li');
    const combined = [...allAnswersParagraphs, ...allAnswersListItems];
    combined.forEach(el => {
        el.innerHTML = el.innerHTML.replace(/&nbsp;/gi, '');
    });

    document.querySelector('.js-pdf').addEventListener('click', () => {
        const content = document.querySelector('.js-pdf-wrapper');
        const title = document.querySelector('.js-pdf-title').innerText;

        const options = {
            margin: 0.4,
            filename: title, // @TODO - change to h1
            pagebreak: {mode: ['avoid-all']}, // automatically adds page-breaks to avoid splitting any elements across pages
            jsPDF: {
                unit: 'in',
                format: 'a4',
                orientation: 'portrait'
            }
        };

        window.html2pdf().set(options).from(content).save();

    });
})();

