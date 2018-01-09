$(document).ready(function () {
    var $lastNameInput = $('#id_last_name');
    var $firstNameInput = $('#id_first_name');
    var $titleInput = $('#id_title');
    var $slugInput = $('#id_slug');

    $firstNameInput.on('input', function () {joinFirstNameLastName();});

    $lastNameInput.on('input', function () {joinFirstNameLastName();});

    function joinFirstNameLastName() {
        var firstName = $firstNameInput.val();
        var lastName = $lastNameInput.val();
        var title = firstName + ' ' + lastName;

        $slugInput.data('previous-val', $slugInput.val());
        $titleInput.data('previous-val', $titleInput.val());
        $titleInput.val(title);
        $titleInput.blur();  // Trigger slug update
    }
});
