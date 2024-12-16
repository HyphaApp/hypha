(function () {
  // Select all rich text answers.
  const richtextanswers = document.querySelector(".rich-text--answers");

  // Select all rich text answers paragraphes.
  const richtextanswers_paras = richtextanswers.querySelectorAll("p");
  richtextanswers_paras.forEach(function (para) {
    // Remove p tags with only whitespace inside.
    if (para.textContent.trim() === "") {
      para.remove();
    }
    // Set dir="auto" so browsers sets the correct directionality (ltr/rtl).
    para.setAttribute("dir", "auto");
  });

  // Select all rich text answers tables.
  const richtextanswers_tables = richtextanswers.querySelectorAll("table");
  // Wrap all tables in a div so overflow auto works.
  richtextanswers_tables.forEach(function (table) {
    const table_wrapper = document.createElement("div");
    table_wrapper.classList.add("rich-text__table");
    table.parentNode.insertBefore(table_wrapper, table);
    table_wrapper.appendChild(table);
  });
})();
