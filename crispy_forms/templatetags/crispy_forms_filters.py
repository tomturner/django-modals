from django import template
from django.forms.formsets import BaseFormSet
from django.utils.safestring import mark_safe

from crispy_forms.helper import FormHelper
from crispy_forms.utils import TEMPLATE_PACK, flatatt, render_crispy_form

register = template.Library()


@register.filter(name="crispy")
def as_crispy_form(form, template_pack=TEMPLATE_PACK):
    if isinstance(form, BaseFormSet):
        return mark_safe(str(form.management_form) + "".join(str(f) for f in form.forms))
    helper = getattr(form, "helper", None) or FormHelper(form)
    helper.form_tag = False
    return render_crispy_form(form, helper=helper)


@register.filter(name="flatatt")
def flatatt_filter(attrs):
    return mark_safe(flatatt(attrs))


@register.filter
def optgroups(field):
    field_id = field.field.widget.attrs.get("id") or field.auto_id
    attrs = {"id": field_id} if field_id else {}
    attrs = field.build_widget_attrs(attrs)
    values = field.field.widget.format_value(field.value())
    return field.field.widget.optgroups(field.html_name, values, attrs)

