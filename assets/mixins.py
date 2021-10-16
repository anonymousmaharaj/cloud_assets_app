import bleach


class RenameObjectMixin:
    """Form Mixin for rename obj."""

    def clean_title(self):
        """Clean new_title field from any HTML tags."""
        return bleach.clean(self.cleaned_data['title'], tags=[], strip=True)
