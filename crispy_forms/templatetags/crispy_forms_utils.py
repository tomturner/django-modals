import re

from django import template
from django.utils.encoding import force_str
from django.utils.functional import keep_lazy

register = template.Library()


@keep_lazy(str)
def remove_spaces(value):
    html = re.sub(r">\s{3,}<", "> <", force_str(value))
    return re.sub(r"/><", "/> <", force_str(html))


class SpecialSpacelessNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        return remove_spaces(self.nodelist.render(context).strip())


@register.tag
def specialspaceless(parser, token):
    nodelist = parser.parse(("endspecialspaceless",))
    parser.delete_first_token()
    return SpecialSpacelessNode(nodelist)

