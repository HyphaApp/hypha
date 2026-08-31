document.addEventListener("alpine:init", () => {
  Alpine.store("multiInput", {
    fields: {},

    initField(fieldId, maxIndex) {
      if (!this.fields[fieldId]) {
        this.fields[fieldId] = {
          visibleCount: 1,
          maxIndex:
            maxIndex !== null ? maxIndex : this.getMaxIndexFromDOM(fieldId),
          initialized: false,
        };
      }

      // Update maxIndex if provided (in case a field with button initializes after others)
      if (maxIndex !== null && this.fields[fieldId].maxIndex < maxIndex) {
        this.fields[fieldId].maxIndex = maxIndex;
      }

      if (!this.fields[fieldId].initialized) {
        this.initializeVisibility(fieldId);
        this.fields[fieldId].initialized = true;
      }
    },

    getMaxIndexFromDOM(fieldId) {
      let maxIndex = 0;
      let element = document.getElementById(`id_${fieldId}_${maxIndex}`);
      while (element) {
        maxIndex++;
        element = document.getElementById(`id_${fieldId}_${maxIndex}`);
      }
      return Math.max(0, maxIndex - 1);
    },

    initializeVisibility(fieldId) {
      const field = this.fields[fieldId];
      if (!field) return;

      let filledCount = 0;
      for (let i = 0; i <= field.maxIndex; i++) {
        const fieldElement = document.getElementById(`id_${fieldId}_${i}`);
        if (fieldElement && fieldElement.value.trim() !== "") {
          filledCount++;
        }
      }
      field.visibleCount = Math.max(1, filledCount);
    },

    isVisible(fieldId, index) {
      const field = this.fields[fieldId];
      return field ? index < field.visibleCount : index === 0;
    },

    showNext(fieldId) {
      const field = this.fields[fieldId];
      if (field && field.visibleCount <= field.maxIndex) {
        field.visibleCount++;
      }
    },

    canAddMore(fieldId) {
      const field = this.fields[fieldId];
      return field ? field.visibleCount <= field.maxIndex : false;
    },
  });
});

function multiInputField(fieldId, fieldName, maxIndex) {
  return {
    fieldId: fieldId,
    fieldIndex: parseInt(fieldName.split("_").pop()),
    maxIndex: maxIndex,

    initField() {
      Alpine.store("multiInput").initField(this.fieldId, this.maxIndex);
    },

    isVisible() {
      return Alpine.store("multiInput").isVisible(
        this.fieldId,
        this.fieldIndex
      );
    },
  };
}
