(function($){
    $(function(){
        var html_str = '<div class="tree-header"><div class="row"><span class="title">' + gettext("Term") +
            '</span><i class="icons fa fa-exclamation-triangle has-system-flags" title="' + gettext("System flags") +
            '"></i><i class="icons fa fa-link is_relation" title="' + gettext("Relation") +
            '"></i><i class="icons fa fa-tags is_mark" title="' + gettext("Mark") +
            '"></i><i class="icons fa fa-list is_characteristic" title="' + gettext("Characteristic") +
            '"></i><i class="icons fa fa-power-off" title="' + gettext("Active") +
            '"></i><span class="view_classes">' + gettext("View Class") + '</span>' +
            '<span class="specification_mode">' + gettext("Specification Mode") + '</span>' +
            '<div><div>'
        $("#tree").before(html_str);
        var html_str = "<div class='help_text'><sup>*</sup>&nbsp;Термины верхнего уровня объединяются семантическим правилом «И»</div>"
        $("#tree").after(html_str);
    });
})(django.jQuery);


