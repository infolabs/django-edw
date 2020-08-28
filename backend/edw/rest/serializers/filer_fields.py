# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import calendar

from django.utils import timezone

from django.utils.translation import ugettext_lazy as _

from rest_framework import fields

from filer.models import Folder, File, Image


class BaseFilerFileField(fields.FileField):
    file_model = File

    def __init__(self, *args, **kwargs):
        self._upload_folder_name = kwargs.pop('upload_folder_name', None)
        super(BaseFilerFileField, self).__init__(*args, **kwargs)

    def get_folder(self, data):
        return Folder.objects.get_or_create(
            name=self._upload_folder_name)[0] if self._upload_folder_name is not None else None

    def get_owner(self, data):
        request = self.context.get('request', None)
        return request.user if request is not None and request.user.is_authenticated() else None

    def get_original_filename(self, data):
        return data.name

    def to_internal_value(self, data):
        return self.file_model.objects.create(file=data, original_filename=self.get_original_filename(data),
                                                    owner=self.get_owner(data), folder=self.get_folder(data))


class BaseFilerImageField(BaseFilerFileField):
    file_model = Image


class FileSorterByDateMixin(object):

    def get_or_create_folder(self, parent, name):
        folder = Folder.objects.filter(parent=parent, name=name)
        return folder[0] if folder else Folder.objects.create(parent=parent, name=name)

    def get_folder(self, data):
        root_folder = BaseFilerFileField.get_folder(self, data)
        current_time = timezone.now()

        year_folder = self.get_or_create_folder(root_folder, '{}'.format(current_time.year))
        month_folder = self.get_or_create_folder(year_folder, _(calendar.month_name[current_time.month]))
        day_folder = self.get_or_create_folder(month_folder, '{:02d}'.format(current_time.day))

        return day_folder


class FilerFileField(FileSorterByDateMixin, BaseFilerFileField):
    pass


class FilerImageField(FileSorterByDateMixin, BaseFilerImageField):
    pass
