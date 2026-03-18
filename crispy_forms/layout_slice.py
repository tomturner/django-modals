from crispy_forms.layout import Field


class LayoutSlice:
    def __init__(self, layout, key=None, field_name=None):
        self.layout = layout
        self.key = key
        self.field_name = field_name
        if isinstance(self.key, int):
            self.key = slice(self.key, self.key + 1, 1)

    def _iter_top_level_indices(self):
        if self.key is None:
            return range(len(self.layout.fields))
        if isinstance(self.key, slice):
            return range(*self.key.indices(len(self.layout.fields)))
        if isinstance(self.key, list):
            return [pointer[0][0] for pointer in self.key if pointer and pointer[0]]
        return []

    def _recursive_field_update(self, layout_object, kwargs):
        if isinstance(layout_object, Field):
            layout_object.update_attributes(**kwargs)
        for child in getattr(layout_object, "fields", []):
            if hasattr(child, "fields") or isinstance(child, Field):
                self._recursive_field_update(child, kwargs)

    def _recursive_named_field_update(self, layout_object, kwargs):
        if isinstance(layout_object, Field) and self.field_name in layout_object.fields:
            layout_object.update_attributes(**kwargs)
        for child in getattr(layout_object, "fields", []):
            if hasattr(child, "fields") or isinstance(child, Field):
                self._recursive_named_field_update(child, kwargs)

    def wrap_together(self, layout_class, *args, **kwargs):
        if self.field_name is not None:
            raise ValueError("wrap_together does not support named-field slices")
        indices = list(self._iter_top_level_indices())
        if not indices:
            return
        start = indices[0]
        fields = [self.layout.fields[i] for i in indices]
        wrapped = layout_class(*fields, *args, **kwargs)
        self.layout.fields[start] = wrapped
        for i in reversed(indices[1:]):
            del self.layout.fields[i]

    def update_attributes(self, **kwargs):
        if self.field_name is not None:
            self._recursive_named_field_update(self.layout, kwargs)
            return
        for i in self._iter_top_level_indices():
            self._recursive_field_update(self.layout.fields[i], kwargs)

