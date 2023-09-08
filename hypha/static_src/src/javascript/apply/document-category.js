// eslint-disable-next-line no-unused-vars
function handleCategory(category) {
    "use strict";

    document.getElementById("id_category").value = category;
    document.getElementsByClassName("form__group id_category")[0].hidden =
        "true";
}
