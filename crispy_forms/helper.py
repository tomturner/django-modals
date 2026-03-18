import re

from crispy_forms.layout import Layout
from crispy_forms.layout_slice import LayoutSlice
from crispy_forms.utils import TEMPLATE_PACK, flatatt, list_difference, render_field


class DynamicLayoutHandler:
    layout = None
    form = None

    def _check_layout(self):
        if self.layout is None:
            raise ValueError("You need to set a layout in your FormHelper")

    def __getitem__(self, key):
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            self._check_layout()
            return LayoutSlice(self.layout, field_name=key)
        return LayoutSlice(self.layout, key=key)

    def __setitem__(self, key, value):
        self.layout[key] = value

    def __delitem__(self, key):
        del self.layout.fields[key]

    def __len__(self):
        return len(self.layout.fields) if self.layout is not None else 0


class FormHelper(DynamicLayoutHandler):
    _form_method = "post"
    _form_action = ""
    _form_style = "default"
    form_id = ""
    form_class = ""
    form_group_wrapper_class = ""
    form_tag = True
    form_error_title = None
    formset_error_title = None
    form_show_errors = True
    render_unmentioned_fields = False
    render_hidden_fields = False
    render_required_fields = False
    _help_text_inline = False
    _error_text_inline = True
    html5_required = False
    form_show_labels = True
    template = None
    field_template = None
    disable_csrf = False
    use_custom_control = True
    label_class = ""
    field_class = ""
    include_media = True
    template_pack = None

    def __init__(self, form=None):
        self.attrs = {}
        self.inputs = []
        if form is not None:
            self.form = form
            self.layout = self.build_default_layout(form)

    def build_default_layout(self, form):
        return Layout(*form.fields.keys())

    @property
    def form_method(self):
        return self._form_method

    @form_method.setter
    def form_method(self, method):
        method = method.lower()
        if method not in ("get", "post"):
            raise ValueError("Only GET and POST are valid form methods")
        self._form_method = method

    @property
    def form_style(self):
        if self._form_style == "default":
            return ""
        if self._form_style == "inline":
            return "inlineLabels"
        return self._form_style

    @form_style.setter
    def form_style(self, style):
        style = style.lower()
        if style not in ("default", "inline"):
            raise ValueError("Only default and inline are valid form styles")
        self._form_style = style

    @property
    def help_text_inline(self):
        return self._help_text_inline

    @help_text_inline.setter
    def help_text_inline(self, flag):
        self._help_text_inline = flag
        self._error_text_inline = not flag

    @property
    def error_text_inline(self):
        return self._error_text_inline

    @error_text_inline.setter
    def error_text_inline(self, flag):
        self._error_text_inline = flag
        self._help_text_inline = not flag

    def add_input(self, input_object):
        self.inputs.append(input_object)

    def add_layout(self, layout):
        self.layout = layout

    def render_layout(self, form, context, template_pack=TEMPLATE_PACK):
        form.rendered_fields = set()
        form.crispy_field_template = self.field_template
        html = self.layout.render(form, self.form_style, context, template_pack=template_pack)
        if self.render_unmentioned_fields or self.render_hidden_fields or self.render_required_fields:
            left_fields = list_difference(tuple(form.fields.keys()), form.rendered_fields)
            for field in left_fields:
                if (
                    self.render_unmentioned_fields
                    or (self.render_hidden_fields and form.fields[field].widget.is_hidden)
                    or (self.render_required_fields and form.fields[field].required)
                ):
                    html += render_field(field, form, self.form_style, context, template_pack=template_pack)
        return html

    def get_attributes(self, template_pack=TEMPLATE_PACK):
        items = {
            "disable_csrf": self.disable_csrf,
            "error_text_inline": self.error_text_inline,
            "field_class": self.field_class,
            "field_template": self.field_template or "%s/field.html" % template_pack,
            "form_method": self.form_method.strip(),
            "form_show_errors": self.form_show_errors,
            "form_show_labels": self.form_show_labels,
            "form_style": self.form_style.strip(),
            "form_tag": self.form_tag,
            "help_text_inline": self.help_text_inline,
            "html5_required": self.html5_required,
            "include_media": self.include_media,
            "label_class": self.label_class,
            "use_custom_control": self.use_custom_control,
        }

        if template_pack == "bootstrap4" and "form-horizontal" in self.form_class.split():
            bootstrap_size_match = re.findall(r"col(-(xl|lg|md|sm))?-(\d+)", self.label_class)
            if bootstrap_size_match:
                items["bootstrap_checkbox_offsets"] = [f"offset{m[0]}-{m[-1]}" for m in bootstrap_size_match]

        items["attrs"] = self.attrs.copy() if self.attrs else {}
        if self.form_id:
            items["attrs"]["id"] = self.form_id.strip()
        if self.form_class:
            items["attrs"]["class"] = self.form_class.strip()
        if self.form_group_wrapper_class:
            items["attrs"]["form_group_wrapper_class"] = self.form_group_wrapper_class

        items["flat_attrs"] = flatatt(items["attrs"])
        if self.inputs:
            items["inputs"] = self.inputs
        if self.form_error_title:
            items["form_error_title"] = self.form_error_title
        if self.formset_error_title:
            items["formset_error_title"] = self.formset_error_title

        for attribute_name, value in self.__dict__.items():
            if (
                attribute_name not in items
                and attribute_name not in ["layout", "inputs"]
                and not attribute_name.startswith("_")
            ):
                items[attribute_name] = value
        return items

