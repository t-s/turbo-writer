CKEDITOR.plugins.add('attach', {
    icons: 'attach',
    init: function (editor) {
        editor.addCommand('insertAttachment', {
            exec: function (editor) {
                modal.open(editor);
            }
        });
        editor.ui.addButton('Attach', {
            label: 'Insert Attachment',
            command: 'insertAttachment',
            toolbar: 'insert'
        });
    }
});

var modal = (function () {
    var
        method = {},
        $overlay,
        $modal,
        $close;

    $overlay = $("#overlay");
    $modal = $("#modal");
    $close = $("#close");

    var editor;

    method.center = function () {
        var top, left;

        top = Math.max($(window).height() - $modal.outerHeight(), 0) / 2;
        left = Math.max($(window).width() - $modal.outerWidth(), 0) / 2;

        $modal.css({
            top: top + $(window).scrollTop(),
            left: left + $(window).scrollLeft()
        });
    };

    method.open = function (arg) {
        editor = arg;

        method.center();

        $(window).bind('resize.modal', method.center);

        $modal.show();
        $overlay.show();

    };

    method.insertAttachment = function (text) {
        editor.insertHtml(text);
        method.close();
    };

    method.close = function () {
        $modal.hide();
        $overlay.hide();
        $(window).unbind('resize.modal');

    };

    $close.click(function (e) {
        e.preventDefault();
        method.close();

    });

    return method;

}());
