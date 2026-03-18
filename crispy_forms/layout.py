from django.template import Context, Template
from django.template.loader import render_to_string
from django.utils.html import conditional_escape

from crispy_forms.utils import TEMPLATE_PACK, flatatt, render_field


def _render_context(context):
    if hasattr(context, "flatten"):
        return context
    return Context(context or {})


class TemplateNameMixin:
    def get_template_name(self, template_pack):
        if "%s" in self.template:
            return self.template % template_pack
        return self.template


class LayoutObject(TemplateNameMixin):
    fields = ()

    def __getitem__(self, item):
        return self.fields[item]

    def __setitem__(self, key, value):
        self.fields[key] = value

    def __delitem__(self, key):
        del self.fields[key]

    def __len__(self):
        return len(self.fields)

    def __getattr__(self, name):
        if "fields" in self.__dict__ and hasattr(self.fields, name):
            return getattr(self.fields, name)
        raise AttributeError(name)

    def get_field_names(self, index=None):
        return self.get_layout_objects(str, index=index, greedy=True)

    def get_layout_objects(self, *layout_classes, **kwargs):
        index = kwargs.pop("index", None) or []
        if not isinstance(index, list):
            index = [index]
        max_level = kwargs.pop("max_level", 0)
        greedy = kwargs.pop("greedy", False)
        pointers = []
        for i, layout_object in enumerate(self.fields):
            if isinstance(layout_object, layout_classes):
                if len(layout_classes) == 1 and layout_classes[0] is str:
                    pointers.append([index + [i], layout_object])
                else:
                    pointers.append([index + [i], layout_object.__class__.__name__.lower()])
            if hasattr(layout_object, "get_layout_objects") and (greedy or len(index) < max_level):
                pointers.extend(
                    layout_object.get_layout_objects(
                        *layout_classes,
                        index=index + [i],
                        max_level=max_level,
                        greedy=greedy,
                    )
                )
        return pointers

    def get_rendered_fields(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        return "".join(
            render_field(field, form, form_style, context, template_pack=template_pack, **kwargs)
            for field in self.fields
        )

    def update_attributes(self, **kwargs):
        for field in self.fields:
            if isinstance(field, Field):
                field.attrs.update(kwargs)
            elif hasattr(field, "update_attributes"):
                field.update_attributes(**kwargs)
            elif hasattr(field, "fields"):
                for nested in field.fields:
                    if hasattr(nested, "update_attributes"):
                        nested.update_attributes(**kwargs)


class Layout(LayoutObject):
    def __init__(self, *fields):
        self.fields = list(fields)

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        return self.get_rendered_fields(form, form_style, context, template_pack=template_pack, **kwargs)


class Div(LayoutObject):
    template = "%s/layout/div.html"

    def __init__(self, *fields, **kwargs):
        self.fields = list(fields)
        self.css_class = kwargs.pop("css_class", None)
        self.css_id = kwargs.pop("css_id", "")
        self.template = kwargs.pop("template", self.template)
        self.flat_attrs = flatatt(kwargs)

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        fields = self.get_rendered_fields(form, form_style, context, template_pack, **kwargs)
        return render_to_string(
            self.get_template_name(template_pack),
            {"div": self, "fields": fields},
        )


class Fieldset(LayoutObject):
    template = "%s/layout/fieldset.html"

    def __init__(self, legend, *fields, **kwargs):
        self.fields = list(fields)
        self.legend = legend
        self.css_class = kwargs.pop("css_class", "")
        self.css_id = kwargs.pop("css_id", None)
        self.template = kwargs.pop("template", self.template)
        self.flat_attrs = flatatt(kwargs)

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        fields = self.get_rendered_fields(form, form_style, context, template_pack, **kwargs)
        legend = ""
        if self.legend:
            legend = Template(str(self.legend)).render(_render_context(context))
        return render_to_string(
            self.get_template_name(template_pack),
            {"fieldset": self, "legend": legend, "fields": fields, "form_style": form_style},
        )


class HTML:
    def __init__(self, html):
        self.html = html

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        return Template(str(self.html)).render(_render_context(context))


class Field(LayoutObject):
    template = "%s/field.html"

    def __init__(self, *args, **kwargs):
        self.fields = list(args)
        self.attrs = {}
        if "css_class" in kwargs:
            self.attrs["class"] = kwargs.pop("css_class")
        self.wrapper_class = kwargs.pop("wrapper_class", None)
        self.template = kwargs.pop("template", self.template)
        self.attrs.update({k.replace("_", "-"): conditional_escape(v) for k, v in kwargs.items()})

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, extra_context=None, **kwargs):
        render_extra_context = extra_context.copy() if extra_context else {}
        if getattr(self, "wrapper_class", None):
            render_extra_context["wrapper_class"] = self.wrapper_class
        return self.get_rendered_fields(
            form,
            form_style,
            context,
            template_pack,
            template=self.get_template_name(template_pack),
            attrs=self.attrs,
            extra_context=render_extra_context,
            **kwargs,
        )

    def update_attributes(self, **kwargs):
        self.attrs.update(kwargs)

