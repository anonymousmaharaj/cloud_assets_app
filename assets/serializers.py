"""All serializers."""
import bleach
from django.contrib.auth.models import User
from django.core import exceptions
from django.utils import timezone
from rest_framework import serializers

from assets import models


class FolderRetrieveUpdateSerializer(serializers.ModelSerializer):
    """Serializer for Get and Update methods."""

    class Meta:
        model = models.Folder
        fields = ('id', 'title',)
        read_only_fields = ('id',)

    def validate_title(self, data):
        """Sanitize the field from HTML tags."""
        return bleach.clean(data, tags=[], strip=True, strip_comments=True)

    def update(self, instance, validated_data):
        """Override this method to validate editable fields."""
        instance.title = validated_data.get('title', instance.title)
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
        fields = ('id', 'title', 'folder', 'size', 'extension')
        read_only_fields = ('id', 'size', 'extension')

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
    """Serializer for List and Create methods for ShareTable."""

    email = serializers.EmailField(write_only=True)

    class Meta:
        model = models.SharedTable
        fields = ('id', 'email', 'expired', 'user', 'file', 'permissions',)
        read_only_fields = ('id', 'user')

    def validate_email(self, data):
        """Validate email field for user exists and sharing with yourself."""
        if not User.objects.filter(email=data).exists():
            raise serializers.ValidationError({'detail': 'User is not exists.'})

        if self.context['request'].user == User.objects.filter(email=data).first():
            raise serializers.ValidationError({'detail': 'Cannot share with yourself.'})

        return bleach.clean(data, tags=[], strip=True, strip_comments=True)

    def validate_expired(self, data):
        if data < timezone.now():
            raise serializers.ValidationError({'detail': 'Cannot be less then now.'})
        return data

    def create(self, validated_data):
        """Override this method to validate exist share."""
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


class ShareUpdateDestroySerializer(serializers.ModelSerializer):
    """Serializer for update and delete share's methods."""

    class Meta:
        model = models.SharedTable
        fields = ('id', 'expired', 'user', 'file', 'permissions',)
        read_only_fields = ('id', 'user', 'file')

    def validate_expired(self, data):
        if data < timezone.now():
            raise serializers.ValidationError({'detail': 'Cannot be less then now.'})
        return data


class ShareFileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for rename file through sharing."""

    class Meta:
        model = models.File
        fields = ('id', 'title',)
        read_only_fields = ('id',)
        extra_kwargs = {'title': {'required': True}}

    def validate_title(self, data):
        return bleach.clean(data, tags=[], strip=True, strip_comments=True)

    def update(self, instance, validated_data):
        """Override update method for rename file."""
        instance.title = validated_data.get('title', instance.title)
        instance.save()
        return instance


class ThumbnailSerializer(serializers.Serializer):
    """Serializer for thumbnail."""

    thumbnail_key = serializers.CharField(required=True)


class RetrieveListSharedFilesSerializer(serializers.ModelSerializer):
    """Serializer for retrieve list of shared files with user."""

    class Meta:
        model = models.SharedTable
        fields = ('id', 'file', 'expired', 'permissions',)
