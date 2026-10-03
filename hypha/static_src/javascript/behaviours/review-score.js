/**
 * Alpine.js data component for calculating review scores in the form.
 * @returns {object} The review score component object.
 */
document.addEventListener("alpine:init", () => {
  Alpine.data("reviewScore", () => {
    return {
      /** @type {number} The calculated review score. */
      totalScore: 0,
      /** @type {number} The average of the valid review scores. */
      averageScore: 0,

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
       * Calculates the total and average score of the selector values.
       * As on the server, n/a (99) and blank answers count as 0.
       */
      calculateScore() {
        const values = [...this.selectors].map((selector) => {
          const value = parseInt(selector.value, 10);
          return Number.isNaN(value) || value === 99 ? 0 : value;
        });

        this.totalScore = values.reduce((sum, value) => sum + value, 0);
        this.averageScore = values.length
          ? Math.round((this.totalScore / values.length) * 10) / 10
          : 0;
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
