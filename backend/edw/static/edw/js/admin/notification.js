/*
* Скрипт для отключения доступных ролей пользователей для уведомления в по выбранным состояниям
*
* */
django.jQuery(function($) {
    'use strict';

    var TransitionSelector = {
        avaliable_roles: {},

        init: function (selector) {
            TransitionSelector.avaliable_roles[selector] = {}
            var $main_el = $('.field-'+selector).first();
            var $target_el = $("[data-source-field='"+selector+"']").first();

            TransitionSelector.avaliable_roles[selector] =  $.parseJSON($target_el.html());
            TransitionSelector.updateTransitions(selector);

            $main_el.find(".selector-add").click(function (event) {
                TransitionSelector.updateTransitions(selector);
            });

            $main_el.find(".selector-remove").click(function (event) {
                TransitionSelector.updateTransitions(selector);
            });

            $main_el.find(".selector-chooseall").click(function (event) {
                TransitionSelector.updateTransitions(selector);
            });

            $main_el.find(".selector-clearall").click(function (event) {
                TransitionSelector.updateTransitions(selector);
            });

        },

        updateTransitions : function (selector) {

            var options = SelectBox.cache['id_'+ selector +'_to'];
            var values = [];
            var avaliable_roles = TransitionSelector.avaliable_roles[selector];
            var roles = [];

            options.forEach(function (item) {
                values.push(item.value);
            });

            if (values.length > 0){
                var first_role = values.pop();
                roles = avaliable_roles[first_role].slice();

                values.forEach(function (item) {
                    var tmp_role = avaliable_roles[item].slice();
                    var tmp_result = [];

                    tmp_role.forEach(function (role) {
                        if (roles.indexOf(role)>-1){
                            tmp_result.push(role);
                        }
                    });
                    roles = tmp_result.slice();
                });
            };

            if (roles.length==0){
                roles.push("0");
            }

            TransitionSelector.set_roles(selector, roles);

        },

        set_roles :function(selector, roles){

            var targetSelector = $("[data-source-field='"+selector+"']").first().data("target-field"),
                $rolesEls = $("input[name='" + targetSelector + "']");

            $rolesEls.each(function () {

                var checkbox_val = $(this).val();

                if(roles.includes(checkbox_val)){

                    $(this).removeAttr('disabled');
                    $(this).parents('li').show();

                }else{

                    $(this).removeAttr('checked');
                    $(this).attr("disabled", true);
                    $(this).parents('li').hide();

                }
                },roles);

            }


    }
    window.TransitionSelector = TransitionSelector;

});