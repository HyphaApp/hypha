/**
 * Alpine.js data component for calculating review scores in the form.
 * @returns {object} The review score component object.
 */
document.addEventListener("alpine:init", () => {
  Alpine.data("reviewScore", () => {
    return {
      /** @type {number} The calculated review score. */
      totalScore: 0,

      /**
       * Initializes the component.
       * Sets up event listeners for score calculation if applicable.
       */
      init() {
        this.selectors = this.$el.querySelectorAll("[data-score-field]");
        if (this.showScore) {
          this.calculateScore();
          this.selectors.forEach((selector) => {
            selector.addEventListener("change", this.calculateScore.bind(this));
          });
        }
      },

      /**
       * Calculates the total score based on valid selector values.
       */
      calculateScore() {
        const validValues = [...this.selectors]
          .map((selector) => parseInt(selector.value))
          .filter((value) => !isNaN(value) && value !== 99);

        this.totalScore = validValues.reduce((sum, value) => sum + value, 0);
      },

      /**
       * Determines if the score should be shown.
       * @returns {boolean} True if there are selectors, false otherwise.
       */
      get showScore() {
        return this.selectors.length > 0;
      },
    };
  });
});
