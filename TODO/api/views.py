from rest_framework import viewsets
from rest_framework import permissions
from django.db.models import Prefetch
from Task.models import Task, Category, Tag, SubTask, Comment, Attachment, TimeLog
from .serializers import (
    TaskListSerializer,
    TaskDetailSerializer,
    CategorySerializer,
    TagSerializer,
    SubTaskSerializer,
    CommentSerializer,
    AttachmentSerializer,
    TimeLogSerializer
)

class IsOwner(permissions.BasePermission):
    """Vérifie que l'utilisateur est propriétaire de la ressource"""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class BaseViewSet(viewsets.ModelViewSet):
    """Classe de base avec permissions et filtrage par utilisateur"""
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TaskViewSet(BaseViewSet):
    queryset = Task.objects.select_related('category', 'user').prefetch_related('tags', 'subtasks')
    
    def get_serializer_class(self):
        return TaskDetailSerializer if self.action == 'retrieve' else TaskListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtres optionnels
        status = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')
        
        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
            
        return queryset

class CategoryViewSet(BaseViewSet):
    queryset = Category.objects.prefetch_related('task_set')
    serializer_class = CategorySerializer

class TagViewSet(BaseViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

class SubTaskViewSet(viewsets.ModelViewSet):
    serializer_class = SubTaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    queryset=SubTask.objects.all()
    def get_queryset(self):
        return SubTask.objects.filter(
            task__user=self.request.user
        ).select_related('task')

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        return Comment.objects.filter(
            task__user=self.request.user
        ).select_related('user', 'task')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        return Attachment.objects.filter(
            task__user=self.request.user
        ).select_related('task')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TimeLogViewSet(viewsets.ModelViewSet):
    serializer_class = TimeLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        return TimeLog.objects.filter(
            task__user=self.request.user
        ).select_related('task')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)