(function($){
    $(function(){
        var html_str = "<div class='help_text'>" +
            "<span><img src='/static/edw/img/admin/semantic_rules/10.png'>&nbsp;" + gettext("Semantic Rule") + ":&nbsp;" + gettext("OR") + "</span><br>" +
            "<span><img src='/static/edw/img/admin/semantic_rules/20.png'>&nbsp;" + gettext("Semantic Rule") + ":&nbsp;" + gettext("XOR") + "</span><br>" +
            "<span><img src='/static/edw/img/admin/semantic_rules/30.png'>&nbsp;" + gettext("Semantic Rule") + ":&nbsp;" + gettext("AND") + "</span><br>" +
            "<span class='footnote'><sup>*</sup>&nbsp;Термины верхнего уровня объединяются семантическим правилом «И»</span>" +
            "</div>"
        $("#tree").after(html_str);
    });
})(django.jQuery);


