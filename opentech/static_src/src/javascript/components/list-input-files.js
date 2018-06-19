import $ from './../globals';

export default function listInputFiles() {
    $('input[type=file]').change(function() {
        // remove any existing files first
        $(this).siblings('.form__file').remove();
        for (let i = 0; i < $(this)[0].files.length; ++i) {
            $(this).parents('.form__item').prepend(`
                <p class="form__file">${$(this)[0].files[i].name}</p>
            `);
        }
    });
}
