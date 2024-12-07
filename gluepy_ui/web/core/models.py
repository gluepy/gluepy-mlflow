from django.db import models


class Run(models.Model):
    run_id = models.CharField(max_length=255)
    run_folder = models.CharField(max_length=255)
    dag = models.CharField(max_length=255)
    config = models.TextField()
    username = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'core'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.run_id} - {self.dag}"


class Metric(models.Model):
    METRIC_TYPES = [
        ('metric', 'Metric'),
        ('param', 'Parameter'),
    ]
    
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name='metrics')
    key = models.CharField(max_length=255)
    value = models.FloatField()
    metric_type = models.CharField(max_length=10, choices=METRIC_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'core'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['run', 'key', 'metric_type']),
        ]

    def __str__(self):
        return f"{self.run.run_id} - {self.key}: {self.value} ({self.metric_type})"


class Artifact(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name='artifacts')
    name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=1000)
    content_type = models.CharField(max_length=255)
    size = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'core'
        ordering = ['name']
        indexes = [
            models.Index(fields=['run', 'name']),
        ]

    def __str__(self):
        return f"{self.run.run_id} - {self.name}"
