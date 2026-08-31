document.addEventListener("htmx:afterRequest", function () {
  const reportDataEl = document.getElementById("reportData");
  if (!reportDataEl || !reportDataEl.textContent) {
    return;
  }
  const reportData = JSON.parse(reportDataEl.textContent);

  // Form inputs
  const frequencyNumberInput = document.getElementById("id_occurrence");
  const frequencyPeriodSelect = document.getElementById("id_frequency");
  const startDateInput = document.getElementById("id_start");
  const doesNotRepeatInput = document.getElementById("id_does_not_repeat");

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
   * Initialize the report frequency configuration form
   * Sets up initial values and event listeners
   */
  function init() {
    if (!frequencyNumberInput || !frequencyPeriodSelect || !startDateInput) {
      return;
    }
    // set project end date
    if (projectEndSlot && reportData.projectEndDate) {
      projectEndSlot.innerHTML = reportData.projectEndDate;
    }
    setFrequency();
    setReportPeriodStart();
    setReportPeriod();

    addFrequencyEvents();
    addReportPeriodEvents();
    setDoesNotRepeat();
  }

  /**
   * Handles the "Does not repeat" checkbox behavior
   * Shows/hides frequency inputs based on checkbox state
   */
  function setDoesNotRepeat() {
    if (!doesNotRepeatInput) {
      return;
    }
    function showHideFrequencyInputs() {
      const elements = document.querySelectorAll(
        ".form__group--report-every, .form__group--schedule, [data-js-report-frequency-card]"
      );
      if (doesNotRepeatInput.checked) {
        elements.forEach((element) => {
          element.style.display = "none";
        });
      } else {
        elements.forEach((element) => {
          element.style.display = "flex";
        });
      }
    }

    showHideFrequencyInputs();
    doesNotRepeatInput.onchange = showHideFrequencyInputs;
  }

  /**
   * Updates frequency display in the UI
   * Sets the frequency number and period text
   */
  function setFrequency() {
    if (
      !frequencyNumberSlot ||
      !frequencyPeriodSlot ||
      !frequencyPeriodSelect ||
      !frequencyNumberInput
    ) {
      return;
    }
    frequencyPeriodSlot.innerHTML = `${frequencyPeriodSelect.value || ""}`;
    frequencyNumberSlot.innerHTML = frequencyNumberInput.value || "";
    pluraliseTimePeriod(frequencyNumberInput.value);
  }

  /**
   * Sets the initial report period start date in the UI
   */
  function setReportPeriodStart() {
    if (!periodStartSlot || !reportData.startDate) {
      return;
    }
    periodStartSlot.innerHTML = new Date(reportData.startDate)
      .toISOString()
      .slice(0, 10);
  }

  /**
   * Updates the report period end date and next report due date in the UI
   */
  function setReportPeriod() {
    if (
      !periodEndSlot ||
      !nextReportDueSlot ||
      !startDateInput ||
      !startDateInput.value
    ) {
      return;
    }

    periodEndSlot.innerHTML = startDateInput.value;

    const daysDiff = dateDiffInDays(new Date(), new Date(startDateInput.value));
    const { weeks, days } = getWeeks(daysDiff);
    const pluraliseWeeks = weeks === 1 ? "" : "s";
    const pluraliseDays = days === 1 ? "" : "s";

    nextReportDueSlot.innerHTML = `${
      weeks > 0 ? `${weeks} week${pluraliseWeeks}` : ""
    } ${days} day${pluraliseDays}`;
  }

  /**
   * Attaches event listeners for report period inputs
   */
  function addReportPeriodEvents() {
    if (startDateInput) {
      startDateInput.oninput = setReportPeriod;
    }
  }

  /**
   * Attaches event listeners for frequency inputs
   */
  function addFrequencyEvents() {
    if (frequencyNumberInput) {
      frequencyNumberInput.oninput = setFrequency;
    }
    if (frequencyPeriodSelect) {
      frequencyPeriodSelect.onchange = setFrequency;
    }
  }

  /**
   * Adds proper pluralization to time period display
   * @param {string|number} number - The frequency number
   */
  function pluraliseTimePeriod(number) {
    if (!frequencyPeriodSlot || !frequencyPeriodSelect) {
      return;
    }
    frequencyPeriodSlot.innerHTML = `${frequencyPeriodSelect.value || ""}${
      Number(number) === 1 ? "" : "s"
    }`;
  }

  /**
   * Calculates the difference in days between two dates
   * @param {Date} startDate - The start date
   * @param {Date} endDate - The end date
   * @returns {number} Number of days between dates
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
   * Converts days to weeks and remaining days
   * @param {number} days - Total days
   * @returns {Object} Object containing weeks and remaining days
   */
  function getWeeks(days) {
    return {
      weeks: Math.floor(days / 7),
      days: days % 7,
    };
  }

  init();
});
