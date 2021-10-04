"""All serializers."""
import bleach
from django.core import exceptions
from django.contrib.auth.models import User
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


class ShareListCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)

    class Meta:
        model = models.SharedTable
        fields = ('id', 'email', 'expired', 'user', 'file', 'permissions',)
        read_only_fields = ('id', 'user')

    def validate_email(self, data):
        if not User.objects.filter(email=data).exists():
            raise serializers.ValidationError({'detail': 'User is not exists.'})
        if self.context['request'].user == User.objects.filter(email=data).first():
            raise serializers.ValidationError({'detail': 'Cannot share with yourself.'})
        return data

    def create(self, validated_data):
        """Override this method to validate exist folder."""
        if models.SharedTable.objects.filter(file=validated_data.get('file').pk,
                                             user=User.objects.filter(
                                                 email=validated_data.get('email')).first()).exists():
            raise serializers.ValidationError({'detail': 'Current share already exists.'})

        instance = models.SharedTable.objects.create(
            file=validated_data.get('file'),
            user=User.objects.filter(email=validated_data.get('email')).first(),
            expired=validated_data.get('expired')
        )
        instance.permissions.set(validated_data.get('permissions'))
        instance.save()

        return instance
