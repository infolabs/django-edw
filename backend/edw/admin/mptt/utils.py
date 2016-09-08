# -*- coding: utf-8 -*-
from django.template.loader import render_to_string
from django.contrib.admin.utils import quote


def get_mptt_admin_node_template(instance):
    '''
    Get MPTT admin node template name by model instance
    :param instance: instance of mptt model
    :return: template name
    '''
    return 'edw/admin/mptt/_%s_node.html' % instance.__class__.__name__.lower()


def mptt_admin_node_info_update_with_template(admin_instance, template, instance, node_info, context={}):
    '''
    Update MPTT admin node with rendered by html template node label.
    :param admin_instance: mptt admin instance
    :param template: template name for renfer
    :param instance: instance of mptt model
    :param node_info: jstree node info
    :param context: additional context for render
    :return: none
    '''

    pk_attname = admin_instance.model._meta.pk.attname
    pk = quote(getattr(instance, pk_attname))

    context.update({
        'instance': instance,
        'node_info': node_info,
        'app_label': instance._meta.app_label.lower()
    })

    label = render_to_string(template, context)

    node_info.update(
        url=admin_instance.get_admin_url('change', (quote(pk),)),
        move_url=admin_instance.get_admin_url('move', (quote(pk),)),
        label=label,
    )
