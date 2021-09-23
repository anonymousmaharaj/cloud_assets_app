"""All serializers."""
import bleach
from django.core import exceptions
from rest_framework import serializers

from assets import models


class FolderRetrieveUpdateSerializer(serializers.ModelSerializer):
    """Serializer for Get and Update methods."""

    class Meta:
        model = models.Folder
        fields = ('id', 'title', 'parent')
        read_only_fields = ('id',)

    def validate_title(self, data):
        """Sanitize the field from HTML tags."""
        return bleach.clean(data, tags=[], strip=True, strip_comments=True)

    def update(self, instance, validated_data):
        """Override this method to validate editable fields."""
        if validated_data.get('parent') is not None:
            if instance == validated_data.get('parent').parent:
                raise serializers.ValidationError({'detail': 'Cannot move folder in this folder.'})

        instance.title = validated_data.get('title', instance.title)
        instance.parent = validated_data.get('parent', instance.parent)
        try:
            instance.clean()
        except exceptions.ValidationError as error:
            raise serializers.ValidationError({'detail': str(error)})
        instance.save()
        return instance


class FileRetrieveUpdateDestroySerializer(serializers.ModelSerializer):
    """Serializer for Get, Update and Delete methods."""

    class Meta:
        model = models.File
        fields = ('id', 'title', 'folder')
        read_only_fields = ('id',)

    def validate_title(self, data):
        """Sanitize the field from HTML tags."""
        return bleach.clean(data, tags=[], strip=True, strip_comments=True)

    def update(self, instance, validated_data):
        """Override this method to validate editable fields."""
        instance.title = validated_data.get('title', instance.title)
        instance.folder = validated_data.get('folder', instance.folder)
        try:
            instance.clean()
        except exceptions.ValidationError as error:
            raise serializers.ValidationError({'detail': str(error)})
        instance.save()
        return instance


class FileListCreateSerializer(serializers.ModelSerializer):
    """Serializer for List and Create methods."""

    class Meta:
        model = models.File
        fields = ('id', 'title', 'folder')
        read_only_fields = ('id',)

    def validate_title(self, data):
        """Sanitize the field from HTML tags."""
        return bleach.clean(data, tags=[], strip=True, strip_comments=True)

    def create(self, validated_data):
        """Override this method to validate exist file."""
        # TODO: add upload file (data)
        if models.File.objects.filter(title=validated_data.get('title'),
                                      owner=validated_data.get('owner'),
                                      folder=validated_data.get('folder')).first():
            raise serializers.ValidationError({'detail': 'Current file already exists.'})
        instance = models.File.objects.create(**validated_data)
        return instance


class FolderListCreateSerializer(serializers.ModelSerializer):
    """Serializer for List and Create methods."""

    class Meta:
        model = models.Folder
        fields = ('title', 'parent')
        read_only_fields = ('owner',)

    def validate_title(self, data):
        """Sanitize the field from HTML tags."""
        return bleach.clean(data, tags=[], strip=True, strip_comments=True)

    def create(self, validated_data):
        """Override this method to validate exist folder."""
        if models.Folder.objects.filter(title=validated_data.get('title'),
                                        owner=validated_data.get('owner'),
                                        parent=validated_data.get('parent')).first():
            raise serializers.ValidationError({'detail': 'Current folder already exists.'})
        instance = models.Folder.objects.create(**validated_data)
        return instance
