from django import forms, template
from django.conf import settings

register = template.Library()


@register.filter
def is_checkbox(field):
    return isinstance(field.field.widget, forms.CheckboxInput)


@register.filter
def is_password(field):
    return isinstance(field.field.widget, forms.PasswordInput)


@register.filter
def is_radioselect(field):
    return isinstance(field.field.widget, forms.RadioSelect) and not isinstance(
        field.field.widget, forms.CheckboxSelectMultiple
    )


@register.filter
def is_select(field):
    return isinstance(field.field.widget, forms.Select)


@register.filter
def is_checkboxselectmultiple(field):
    return isinstance(field.field.widget, forms.CheckboxSelectMultiple)


@register.filter
def is_file(field):
    return isinstance(field.field.widget, forms.FileInput)


@register.filter
def is_clearable_file(field):
    return isinstance(field.field.widget, forms.ClearableFileInput)


@register.filter
def is_multivalue(field):
    return isinstance(field.field.widget, forms.MultiWidget)


@register.filter
def classes(field):
    return field.widget.attrs.get("class", None)


@register.filter
def css_class(field):
    return field.field.widget.__class__.__name__.lower()


def pairwise(iterable):
    iterator = iter(iterable)
    return zip(iterator, iterator)


class CrispyFieldNode(template.Node):
    def __init__(self, field, attrs):
        self.field = field
        self.attrs = attrs

    def render(self, context):
        if self not in context.render_context:
            context.render_context[self] = (template.Variable(self.field), self.attrs)

        field, attrs = context.render_context[self]
        field = field.resolve(context)

        widgets = getattr(field.field.widget, "widgets", [getattr(field.field.widget, "widget", field.field.widget)])
        if isinstance(attrs, dict):
            attrs = [attrs] * len(widgets)

        converters = {
            "textinput": "textinput textInput",
            "fileinput": "fileinput fileUpload",
            "passwordinput": "textinput textInput",
        }
        converters.update(getattr(settings, "CRISPY_CLASS_CONVERTERS", {}))

        for widget, attr in zip(widgets, attrs):
            class_name = converters.get(widget.__class__.__name__.lower(), widget.__class__.__name__.lower())
            css_class = widget.attrs.get("class", "")
            if css_class:
                if class_name not in css_class:
                    css_class += " %s" % class_name
            else:
                css_class = class_name
            widget.attrs["class"] = css_class

            for attribute_name, attribute in attr.items():
                resolved_attribute_name = template.Variable(attribute_name).resolve(context)
                resolved_attribute_value = template.Variable(attribute).resolve(context)
                if resolved_attribute_name in widget.attrs:
                    for attr_value in str(resolved_attribute_value).split():
                        if attr_value not in str(widget.attrs[resolved_attribute_name]).split():
                            widget.attrs[resolved_attribute_name] += " " + attr_value
                else:
                    widget.attrs[resolved_attribute_name] = resolved_attribute_value
        return str(field)


@register.tag(name="crispy_field")
def crispy_field(parser, token):
    parts = token.split_contents()
    if len(parts) < 2:
        raise template.TemplateSyntaxError("Usage: {% crispy_field field [attr value ...] %}")
    field = parts[1]
    attrs = {}
    for attribute_name, value in pairwise(parts[2:]):
        attrs[attribute_name] = value
    return CrispyFieldNode(field, attrs)

