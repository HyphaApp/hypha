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
        if (!form.initUploadFieldsDone && form.querySelector('[name=create_vendor_view-current_step]')) {
            initWizard(form);
            form.initUploadFieldsDone = true;
        }
    });

    function init(form) {
        if ($('.form__group--file').length){
            window.initUploadFields(form);

            // Hide wrapper elements for hidden inputs added by django-file-form
            $('input[type=hidden]').closest('.form__group').hide();
        }
    }

    // Initilise multi-step wizard forms
    function initWizard(form) {
        const step = form.querySelector('[name=create_vendor_view-current_step]').value;
        if (step === 'documents') {
            window.initUploadFields(
                form,
                {
                    prefix: 'documents'
                }
            );
            // Hide wrapper elements for hidden inputs added by django-file-form
            $('input[type=hidden]').closest('.form__group').hide();
        }
    }
});
