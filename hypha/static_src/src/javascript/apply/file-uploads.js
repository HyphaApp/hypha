jQuery(function ($) {

    'use strict';

    // django-file-form
    $('form').get().forEach(function (e) {
        // Prevent initilising it multiple times and run it for forms
        // that have a `form_id` field added by django-file-form.
        if (!e.initUploadFieldsDone && e.querySelector('[name=form_id]')) {
            window.initUploadFields(e);
            e.initUploadFieldsDone = true;
        }
    });
    $('input[type=hidden]').closest('.form__group').hide();

    // TODO: check what we else need from this file
    return; /* eslint-disable */

    $('.form__group--file').each(function () {
        var $file_field = $(this);
        var $file_input = $file_field.find('input[type="file"]');
        var $file_list = $file_field.find('.form__file-list');
        // var $file_drop = $file_field.find('.form__file-drop-zone');

        $file_input.on('change', function (e) {
            e.stopPropagation();
            e.preventDefault();

            var files = $(this).prop('files');
            var output = fileList(files);
            $file_list.html('<ul>' + output.join('') + '</ul>');
        });

        /*
        $file_drop.on('dragover', function (e) {
            e.stopPropagation();
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
        });

        $file_drop.on('drop', function (e) {
            e.stopPropagation();
            e.preventDefault();
            var files = e.dataTransfer.file;
            var output = fileList(files);
            $file_list.html('<ul>' + output.join('') + '</ul>');
        });
        */
    });

    function fileList(files) {
        var output = [];
        for (var i = 0, f, len = files.length; i < len; i++) {
            f = files[i];
            output.push('<li><strong>', f.name, '</strong> (', f.type || 'n/a', ') - ', formatBytes(f.size), '</li>');
        }
        return output;
    }

    function formatBytes(bytes, decimals) {
        if (bytes === 0) {
            return '0 Bytes';
        }
        var k = 1024;
        var dm = decimals <= 0 ? 0 : decimals || 2;
        var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
        var i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

});
