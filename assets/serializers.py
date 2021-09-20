"""All serializers."""

from rest_framework import serializers

from assets import models


class UpdateFolderSerializer(serializers.ModelSerializer):
    """Serializer for rename folder's title."""

    class Meta:
        model = models.Folder
        fields = ('id', 'title')

    def validate_title(self, title):
        """Check the new folder title.

        Return ValidationError if in parent folder already exists other folder with current title.
        """
        qs = models.Folder.objects.filter(parent=self.instance.parent,
                                          title=title,
                                          owner=self.instance.owner).exists()
        if qs:
            raise serializers.ValidationError('Already exists.')
        return title
