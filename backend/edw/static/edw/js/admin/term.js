(function($){
    "use strict";
    $(function(){
        var html_str = "<div class='help_text'>" +
            "<p><img src='/static/edw/img/admin/semantic_rules/10.png'>&nbsp;" + gettext("Semantic Rule") + ":&nbsp;" + gettext("OR") + "<br/>" +
            "<img src='/static/edw/img/admin/semantic_rules/20.png'>&nbsp;" + gettext("Semantic Rule") + ":&nbsp;" + gettext("XOR") + "<br/>" +
            "<img src='/static/edw/img/admin/semantic_rules/30.png'>&nbsp;" + gettext("Semantic Rule") + ":&nbsp;" + gettext("AND") + "<br/>" +
            "<span class='footnote'><sup>*</sup>&nbsp;Термины верхнего уровня объединяются семантическим правилом «И»</span></p>" +
            "</div>";
        $("#tree").after(html_str);
    });
})(django.jQuery || jQuery);
