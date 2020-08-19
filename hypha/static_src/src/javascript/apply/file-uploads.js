jQuery(function ($) {
    'use strict';

    // Initialize django-file-form
    $('form').get().forEach(function (form) {
        // Prevent initilising it multiple times and run it for forms
        // that have a `form_id` field added by django-file-form.
        if (!form.initUploadFieldsDone && form.querySelector('[name=form_id]')) {
            init(form);
            form.initUploadFieldsDone = true;
        }
    });

    function init(form) {
        window.initUploadFields(form);

        // Hide wrapper elements for hidden inputs added by django-file-form
        $('input[type=hidden]').closest('.form__group').hide();

        // For each file field in the form show warning when dropping files with an invalid file extension.
        $('[type=file]', form).get().forEach(function (fileField) {
            var allowedExtensions = fileField.accept.split(', ');

            $(fileField).next('.dff-files').on('drop', function (e) {
                var items = e.originalEvent.dataTransfer.items;
                var files = e.originalEvent.dataTransfer.files;
                for (var i = 0; i < items.length; i++) {
                    var extension = '.' + files[i].name.split('.').slice(-1)[0];
                    if (!allowedExtensions.includes(extension)) {
                        let warning = e.currentTarget.querySelector('.invalid-file-warning');
                        // Only add the warning when it's not present.
                        if (warning == null) {
                            var span = document.createElement('span');
                            span.setAttribute('class', 'invalid-file-warning');
                            var text = document.createTextNode(
                                'Warning: Invalid files were detected, please delete before submitting.'
                            );
                            span.appendChild(text);
                            span.style.color = 'red';
                            e.currentTarget.appendChild(span);
                            break;
                        }
                    }
                }
            });
        });
    }

});
