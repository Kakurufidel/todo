from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

class BaseModel(models.Model):
    """
    Modèle de base abstrait avec des champs temporels communs
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)

class SoftDeleteModel(models.Model):
    """
    Modèle abstrait pour la suppression douce
    """
    deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    def soft_delete(self):
        self.deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def restore(self):
        self.deleted = False
        self.deleted_at = None
        self.save()
    
    class Meta:
        abstract = True

class Category(BaseModel, SoftDeleteModel):
    """
    Catégories pour organiser les tâches
    """
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

    @property
    def task_count(self):
        return self.task_set.filter(deleted=False).count()

class Tag(BaseModel, SoftDeleteModel):
    """
    Étiquettes pour classer les tâches
    """
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.name} ({self.color})" if self.color else self.name

class Task(BaseModel, SoftDeleteModel):
    """
    Modèle principal des tâches avec rappel automatique intégré
    """
    PRIORITY_CHOICES = [
        ('low', 'Faible'),
        ('medium', 'Moyenne'), 
        ('high', 'Haute')
    ]
    
    STATUS_CHOICES = [
        ('todo', 'À faire'),
        ('in_progress', 'En cours'),
        ('done', 'Terminée')
    ]

    # Champs principaux
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Relations
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    
    # Gestion des rappels automatiques
    auto_reminder = models.BooleanField(default=True, verbose_name="Rappel automatique")
    reminder_offset = models.DurationField(default=timedelta(hours=1), verbose_name="Délai avant rappel")

    def clean(self):
        """Validation des données avant sauvegarde"""
        if self.due_date and self.reminder_offset >= (self.due_date - timezone.now()):
            raise ValidationError("Le rappel doit être configuré avant la date d'échéance")

    def save(self, *args, **kwargs):
        """Sauvegarde avec création automatique du rappel"""
        self.clean()
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        # Création automatique du rappel si configuré
        if is_new and self.auto_reminder and self.due_date:
            Reminder.objects.create(
                task=self,
                user=self.user,
                time=self.due_date - self.reminder_offset
            )

    @property
    def is_overdue(self):
        """Vérifie si la tâche est en retard"""
        return bool(
            self.due_date and 
            self.due_date < timezone.now() and 
            self.status != 'done' and
            not self.deleted
        )

    @property
    def time_remaining(self):
        """Calcule le temps restant avant échéance"""
        return self.due_date - timezone.now() if self.due_date else None

    def complete(self):
        """Marque la tâche comme terminée"""
        self.status = 'done'
        self.save()

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

class Reminder(BaseModel):
    """
    Rappel automatiquement créé pour les tâches
    """
    task = models.OneToOneField(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        related_name='task_reminder'
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    time = models.DateTimeField()
    notified = models.BooleanField(default=False)

    @property
    def is_upcoming(self):
        """Vérifie si le rappel est dans les prochaines 24h"""
        now = timezone.now()
        return now <= self.time <= now + timedelta(hours=24)

    def __str__(self):
        return f"Rappel pour {self.task.title if self.task else 'Tâche supprimée'} à {self.time}"

class SubTask(BaseModel, SoftDeleteModel):
    """
    Sous-tâches pour décomposer les tâches principales
    """
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, related_name='subtasks')
    title = models.CharField(max_length=100)
    completed = models.BooleanField(default=False)

    def toggle_completion(self):
        """Basculer l'état de complétion"""
        self.completed = not self.completed
        self.save()

    def __str__(self):
        status = "✓" if self.completed else "✗"
        return f"{status} {self.title}"

class Comment(BaseModel, SoftDeleteModel):
    """
    Commentaires sur les tâches
    """
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()

    @property
    def preview(self):
        """Aperçu raccourci du commentaire"""
        return (self.content[:50] + '...') if len(self.content) > 50 else self.content

    def __str__(self):
        return f"Commentaire par {self.user.username if self.user else 'Utilisateur supprimé'}"

class Attachment(BaseModel, SoftDeleteModel):
    """
    Fichiers joints aux tâches
    """
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, related_name='attachments')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to='attachments/')
    name = models.CharField(max_length=100, blank=True)

    @property
    def file_url(self):
        """URL d'accès au fichier"""
        return self.file.url if self.file else None

    def save(self, *args, **kwargs):
        """Sauvegarde avec nom de fichier automatique"""
        if not self.name and self.file:
            self.name = self.file.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or f"Fichier #{self.id}"

class TimeLog(BaseModel, SoftDeleteModel):
    """
    Suivi du temps passé sur les tâches
    """
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, related_name='time_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    @property
    def duration(self):
        """Calcule la durée entre start_time et end_time"""
        if self.end_time:
            return self.end_time - self.start_time
        return None

    def stop_timer(self):
        """Arrête le chronomètre"""
        if not self.end_time:
            self.end_time = timezone.now()
            self.save()

    def __str__(self):
        return f"Temps enregistré: {self.duration}" if self.duration else "Chronomètre en cours"