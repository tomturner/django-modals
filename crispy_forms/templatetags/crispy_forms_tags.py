from django import template

from crispy_forms.utils import render_crispy_form
from crispy_forms.templatetags import crispy_forms_filters
from crispy_forms.templatetags.crispy_forms_filters import *  # noqa: F401,F403

register = crispy_forms_filters.register


class CrispyNode(template.Node):
    def __init__(self, form, helper=None):
        self.form = template.Variable(form)
        self.helper = template.Variable(helper) if helper else None

    def render(self, context):
        form = self.form.resolve(context)
        helper = self.helper.resolve(context) if self.helper else None
        return render_crispy_form(form, helper=helper, context=context)


@register.tag(name="crispy")
def do_crispy(parser, token):
    parts = token.split_contents()
    if len(parts) not in (2, 3):
        raise template.TemplateSyntaxError("Usage: {% crispy form [helper] %}")
    if len(parts) == 2:
        return CrispyNode(parts[1])
    return CrispyNode(parts[1], parts[2])

