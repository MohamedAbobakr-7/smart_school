from django.db import models


class SchoolClass(models.Model):
    """
    Represents a class/grade group in the school.
    Examples: "Grade 5 - A", "Grade 10 - B"
    """

    name = models.CharField(
        max_length=100,
        help_text='Grade/class name (e.g., Grade 5, Year 10)'
    )

    section = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text='Section label (e.g., A, B, C). Leave blank for no section.'
    )

    description = models.TextField(
        blank=True,
        default='',
        help_text='Optional description or notes about this class.'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'school_classes'
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'
        ordering = ['name', 'section']
        unique_together = [['name', 'section']]
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['section']),
        ]

    def __str__(self):
        if self.section:
            return f"{self.name} - {self.section}"
        return self.name

    @property
    def display_name(self):
        """Full display name combining name and section."""
        if self.section:
            return f"{self.name} - {self.section}"
        return self.name
