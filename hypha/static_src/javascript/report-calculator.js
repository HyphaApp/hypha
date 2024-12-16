document.addEventListener("htmx:afterRequest", function () {
  const reportDataEl = document.getElementById("reportData");
  if (!reportDataEl) {
    return;
  }
  const reportData = JSON.parse(reportDataEl.textContent);

  // Form inputs
  const frequencyNumberInput = document.getElementById("id_occurrence");
  const frequencyPeriodSelect = document.getElementById("id_frequency");
  const startDateInput = document.getElementById("id_start");

  // Form slots
  const projectEndSlot = document.querySelector(".js-project-end-slot");
  const frequencyNumberSlot = document.querySelector(
    ".js-frequency-number-slot"
  );
  const frequencyPeriodSlot = document.querySelector(
    ".js-frequency-period-slot"
  );
  const periodStartSlot = document.querySelector(".js-report-period-start");
  const periodEndSlot = document.querySelector(".js-report-period-end");
  const nextReportDueSlot = document.querySelector(".js-next-report-due-slot");

  /**
   * Set initial values & setup event listeners
   */
  function init() {
    // Set on page load
    setProjectEnd();
    setFrequency();
    setReportPeriodStart();
    setReportPeriod();

    // Add event listeners
    addFrequencyEvents();
    addReportPeriodEvents();
  }

  /**
   * Sets the project end date in the form info box
   */
  function setProjectEnd() {
    projectEndSlot.innerHTML = reportData.projectEndDate;
  }

  /**
   * Set the reporting frequency
   */
  function setFrequency() {
    frequencyPeriodSlot.innerHTML = `${frequencyPeriodSlot.value}`;
    frequencyNumberSlot.innerHTML = frequencyNumberInput.value;
    pluraliseTimePeriod(frequencyNumberInput.value);
  }

  /**
   * Set the reporting period start date
   */
  function setReportPeriodStart() {
    const startDate = new Date(reportData.startDate);
    periodStartSlot.innerHTML = startDate.toISOString().slice(0, 10);
  }

  /**
   * Set the reporting period
   */
  function setReportPeriod() {
    // Update the reporting period end date (next report date)
    periodEndSlot.innerHTML = startDateInput.value;

    // Update the reporting period range (next report date - today)
    const daysDiff = dateDiffInDays(new Date(), new Date(startDateInput.value));
    const weeksAndDays = getWeeks(daysDiff);
    const { weeks, days } = weeksAndDays;
    const pluraliseWeeks = weeks === 1 ? "" : "s";
    const pluraliseDays = days === 1 ? "" : "s";

    nextReportDueSlot.innerHTML = `
                ${
                  weeks > 0 ? `${weeks} week${pluraliseWeeks}` : ""
                } ${days} day${pluraliseDays}
            `;
  }

  /**
   * Set report period once start date receives input
   */
  function addReportPeriodEvents() {
    startDateInput.addEventListener("input", () => {
      setReportPeriod();
    });
  }

  /**
   * Update reporting frequency as the options are changed
   */
  function addFrequencyEvents() {
    frequencyNumberInput.addEventListener("input", () => {
      setFrequency();
    });

    frequencyPeriodSelect.addEventListener("change", () => {
      setFrequency();
    });
  }

  /**
   * Adds an "s" to the frequencyPeriodSelect text if plural, removes "s" otherwise.
   *
   * @param {number} number - number to determine plural for
   */
  function pluraliseTimePeriod(number) {
    frequencyPeriodSlot.innerHTML = `${frequencyPeriodSelect.value}${
      Number(number) === 1 ? "" : "s"
    }`;
  }

  /**
   * Get the difference of days between two dates
   *
   * @param {Date} startDate - the subtrahend date
   * @param {Date} endDate - the minuend date
   *
   * @returns {number} Difference of days betwen the given dates
   */
  function dateDiffInDays(startDate, endDate) {
    const msPerDay = 1000 * 60 * 60 * 24;
    const utc1 = Date.UTC(
      startDate.getFullYear(),
      startDate.getMonth(),
      startDate.getDate()
    );
    const utc2 = Date.UTC(
      endDate.getFullYear(),
      endDate.getMonth(),
      endDate.getDate()
    );

    return Math.floor((utc2 - utc1) / msPerDay);
  }

  /**
   * Convert days into weeks and days
   *
   * @param {number} days - number of days
   *
   * @returns {{weeks: number, days: number}} number of weeks & days
   */
  function getWeeks(days) {
    return {
      weeks: Math.floor(days / 7),
      days: days % 7,
    };
  }

  init();
});
