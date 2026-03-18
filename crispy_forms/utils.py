from functools import lru_cache

from django.conf import settings
from django.forms.formsets import BaseFormSet
from django.forms.utils import flatatt as _flatatt
from django.template.loader import get_template, render_to_string
from django.utils.functional import SimpleLazyObject
from django.utils.safestring import mark_safe


def get_template_pack():
    return getattr(settings, "CRISPY_TEMPLATE_PACK", "bootstrap4")


TEMPLATE_PACK = SimpleLazyObject(get_template_pack)


def _context_to_dict(context):
    if context is None:
        return {}
    if hasattr(context, "flatten"):
        return context.flatten()
    return dict(context)


@lru_cache()
def default_field_template(template_pack=TEMPLATE_PACK):
    return get_template("%s/field.html" % template_pack)


def flatatt(attrs):
    return _flatatt({k.replace("_", "-"): v for k, v in attrs.items()})


def render_field(
    field,
    form,
    form_style,
    context,
    template=None,
    labelclass=None,
    layout_object=None,
    attrs=None,
    template_pack=TEMPLATE_PACK,
    extra_context=None,
    **kwargs,
):
    if field is None:
        return ""

    if hasattr(field, "render"):
        return field.render(form, form_style, context, template_pack=template_pack, **kwargs)

    bound_field = form[field]
    field_instance = bound_field.field
    if attrs:
        widgets = getattr(field_instance.widget, "widgets", [field_instance.widget])
        widget_attrs = attrs if isinstance(attrs, list) else [attrs] * len(widgets)
        for widget, attr in zip(widgets, widget_attrs):
            widget.attrs.update(attr)

    if hasattr(form, "rendered_fields"):
        form.rendered_fields.add(field)

    if template is None:
        if getattr(form, "crispy_field_template", None):
            template = get_template(form.crispy_field_template)
        else:
            template = default_field_template(template_pack)
    else:
        template = get_template(template)

    if layout_object is not None:
        if hasattr(layout_object, "bound_fields") and isinstance(layout_object.bound_fields, list):
            layout_object.bound_fields.append(bound_field)
        else:
            layout_object.bound_fields = [bound_field]

    template_context = _context_to_dict(context)
    template_context.update(
        {
            "field": bound_field,
            "labelclass": labelclass,
            "flat_attrs": flatatt(attrs if isinstance(attrs, dict) else {}),
        }
    )
    if extra_context:
        template_context.update(extra_context)
    return template.render(template_context)


def render_crispy_form(form, helper=None, context=None):
    from crispy_forms.helper import FormHelper

    helper = helper or getattr(form, "helper", None) or FormHelper(form)
    template_pack = str(getattr(helper, "template_pack", TEMPLATE_PACK))
    attrs = helper.get_attributes(template_pack=template_pack)

    render_context = _context_to_dict(context)
    render_context.update(attrs)
    render_context.setdefault("form_show_errors", True)
    render_context.setdefault("form_show_labels", True)

    if isinstance(form, BaseFormSet):
        render_context["formset"] = form
        if helper.template:
            return render_to_string(helper.template, render_context)
        return mark_safe(str(form.management_form) + "".join(str(f) for f in form.forms))

    render_context["form"] = form
    if helper.layout:
        form.rendered_fields = set()
        form.crispy_field_template = helper.field_template
        form_html = helper.render_layout(form, render_context, template_pack=template_pack)
    else:
        form_html = str(form)

    if attrs.get("inputs"):
        render_context["inputs"] = attrs["inputs"]
        form_html += render_to_string("%s/inputs.html" % template_pack, render_context)

    if helper.template:
        render_context["form_html"] = mark_safe(form_html)
        return render_to_string(helper.template, render_context)

    if not attrs.get("form_tag", True):
        return mark_safe(form_html)

    csrf_html = ""
    csrf_token = render_context.get("csrf_token")
    if csrf_token and not attrs.get("disable_csrf"):
        csrf_html = (
            '<input type="hidden" name="csrfmiddlewaretoken" value="%s">' % csrf_token
        )
    flat_attrs = attrs.get("flat_attrs", "")
    return mark_safe("<form%s>%s%s</form>" % (flat_attrs, csrf_html, form_html))


def list_difference(left, right):
    blocked = set(right)
    difference = []
    for item in left:
        if item not in blocked:
            blocked.add(item)
            difference.append(item)
    return difference

