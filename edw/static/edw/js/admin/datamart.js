(function($){
    $(function(){
        var html_str = '<div class="tree-header"><div class="row"><span class="title">' + gettext("Data mart") +
            '</span><i class="icons fa fa-exclamation-triangle has-system-flags" title="' + gettext("System flags") +
            '"></i><i class="icons fa fa-power-off" title="' + gettext("Active") +
            '"></i><span class="view_classes">' + gettext("View Class") + '</span>' +
            '<div><div>'
        $("#tree").before(html_str);
    });
})(django.jQuery);


