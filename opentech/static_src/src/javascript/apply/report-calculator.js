(function ($) {

    'use strict';

    const reportData = JSON.parse(document.getElementById('lastReportData').textContent);

    // Form inputs
    const frequencyNumberInput = document.getElementById('id_occurrence');
    const frequencyPeriodSelect = document.getElementById('id_frequency');
    const startDateInput = document.getElementById('id_start');

    // Form slots
    const projectEndSlot = document.querySelector('.js-project-end-slot');
    const frequencyNumberSlot = document.querySelector('.js-frequency-number-slot');
    const frequencyPeriodSlot = document.querySelector('.js-frequency-period-slot');
    const periodStartSlot = document.querySelector('.js-report-period-start');
    const periodEndSlot = document.querySelector('.js-report-period-end');


    function init() {
        console.log(reportData);
        // Set on page load
        setProjectEnd();
        setFrequency();
        setReportPeriodStart();

        // Add event listeners
        addFrequencyEvents();
        addReportPeriodEvents();
    }

    // Sets the project end date in the form info box
    function setProjectEnd() {
        projectEndSlot.innerHTML = reportData.projectEndDate;
    }

    // Set the reporting frequency
    function setFrequency() {
        frequencyNumberSlot.innerHTML = frequencyNumberInput.value;
        frequencyPeriodSlot.innerHTML = frequencyPeriodSelect.value;
    }

    // Set the reporting period start date (endDate + 1)
    function setReportPeriodStart() {
        const endDate = new Date(reportData.endDate);
        endDate.setDate(endDate.getDate() + 1);
        periodStartSlot.innerHTML = endDate.toISOString().slice(0, 10);
    }

    // Update the reporting period end date (next report date)
    function addReportPeriodEvents() {
        startDateInput.oninput = e => {
            periodEndSlot.innerHTML = e.target.value;
        };
    }

    // Update reporting frequency as the options are changed
    function addFrequencyEvents() {
        frequencyNumberInput.oninput = e => {
            frequencyNumberSlot.innerHTML = e.target.value;
            pluraliseTimePeriod(e.target.value);
        };

        frequencyPeriodSelect.onchange = e => {
            frequencyPeriodSlot.innerHTML = `${e.target.value}`;
            pluraliseTimePeriod(frequencyNumberInput.value);
        };
    }

    function pluraliseTimePeriod(number) {
        frequencyPeriodSlot.innerHTML = `${frequencyPeriodSelect.value}${Number(number) === 1 ? '' : 's'}`;
    }

    init();

})(jQuery);


// next report date - today = due period
