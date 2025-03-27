from rest_framework import serializers
from Task.models import *
from django.contrib.auth import get_user_model

User = get_user_model()
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        extra_kwargs = {'password': {'write_only': True}}

class SubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTask
        fields = ['id', 'title', 'completed']

class TaskListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes"""
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'priority', 'status', 'due_date', 'is_overdue']

class TaskDetailSerializer(serializers.ModelSerializer):
    """Version détaillée avec relations"""
    subtasks = SubTaskSerializer(many=True, read_only=True)
    time_remaining = serializers.DurationField(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'priority', 'status',
            'due_date', 'time_remaining', 'category', 'tags', 'subtasks'
        ]

class CategorySerializer(serializers.ModelSerializer):
    task_count = serializers.IntegerField(source='task_set.count', read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'task_count']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color']

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(source='user.username')
    
    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'created_at']

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'name', 'file', 'created_at']

class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = ['id', 'time', 'notified']

class TimeLogSerializer(serializers.ModelSerializer):
    duration = serializers.DurationField(read_only=True)
    
    class Meta:
        model = TimeLog
        fields = ['id', 'start_time', 'end_time', 'duration']