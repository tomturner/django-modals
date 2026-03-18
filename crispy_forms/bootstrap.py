from django.template import Context, Template
from django.template.loader import render_to_string

from crispy_forms.layout import TemplateNameMixin
from crispy_forms.utils import TEMPLATE_PACK, flatatt


class StrictButton(TemplateNameMixin):
    template = "%s/layout/button.html"
    field_classes = "btn"

    def __init__(self, content, **kwargs):
        self.content = content
        self.template = kwargs.pop("template", self.template)
        kwargs.setdefault("type", "button")
        if "css_id" in kwargs:
            kwargs["id"] = kwargs.pop("css_id")
        kwargs["class"] = self.field_classes
        if "css_class" in kwargs:
            kwargs["class"] += " %s" % kwargs.pop("css_class")
        self.flat_attrs = flatatt(kwargs)

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        if hasattr(context, "flatten"):
            template_context = context.flatten()
            context_obj = context
        else:
            template_context = dict(context or {})
            context_obj = Context(template_context)
        self.content = Template(str(self.content)).render(context_obj)
        template_context["button"] = self
        return render_to_string(self.get_template_name(template_pack), template_context)

