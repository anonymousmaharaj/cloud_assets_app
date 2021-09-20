"""All serializers."""

from django.core import exceptions
from rest_framework import serializers

from assets import models


class UpdateFolderSerializer(serializers.ModelSerializer):
    """Serializer for rename folder's title."""

    id = serializers.ReadOnlyField(source='pk')

    class Meta:
        model = models.Folder
        fields = ('id', 'title')

    def update(self, instance, validated_data):
        instance.title = validated_data['title']
        try:
            instance.clean()
        except exceptions.ValidationError as error:
            raise serializers.ValidationError(str(error))
        instance.save()
        return instance
