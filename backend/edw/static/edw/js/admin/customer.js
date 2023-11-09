var djangoQquery = django.jQuery || $;
djangoQquery(function($) {
  'use strict';
  $('fieldset.module.aligned:first-child').before($('#customer-group'));
});
