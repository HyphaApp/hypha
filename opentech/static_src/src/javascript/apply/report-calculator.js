(function ($) {

    'use strict';

    const reportData = JSON.parse(document.getElementById('lastReportData').textContent);

    // Form inputs
    const frequencyNumberInput = document.getElementById('id_occurrence');
    const frequencyPeriodSelect = document.getElementById('id_frequency');

    // Form info slots
    const projectEndSlot = document.querySelector('.js-project-end-slot');
    const frequencyNumberSlot = document.querySelector('.js-frequency-number-slot');
    const frequencyPeriodSlot = document.querySelector('.js-frequency-period-slot');


    function init() {
        console.log(reportData);
        setProjectEnd();
        setFrequency();
        addFrequencyEvents();

    }

    // Sets the project end date in the form info box
    function setProjectEnd() {
        projectEndSlot.innerHTML = reportData.projectEndDate;
    }

    // Set the reporting frequency on page load
    function setFrequency() {
        frequencyNumberSlot.innerHTML = frequencyNumberInput.value;
        frequencyPeriodSlot.innerHTML = frequencyPeriodSelect.value;
    }

    // Update reporting frequency as the options are changed
    function addFrequencyEvents() {
        frequencyNumberInput.oninput = e => {
            frequencyNumberSlot.innerHTML = e.target.value;

            checkIfPlural(e.target.value);
        };

        frequencyPeriodSelect.onchange = e => {
            frequencyPeriodSlot.innerHTML = `${e.target.value}`;
            checkIfPlural(frequencyNumberInput.value);
        };
    }

    function checkIfPlural(number) {
        frequencyPeriodSlot.innerHTML = `${frequencyPeriodSelect.value}${Number(number) === 1 ? '' : 's'}`;
    }

    init();

})(jQuery);


// next report date - today = due period
