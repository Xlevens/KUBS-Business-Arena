from django.db import models
from django.contrib.auth.models import User


class Event(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Round(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rounds')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    round_head = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_rounds',
    )
    leaderboard_visible = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event.name} - {self.name}"


class Contestant(models.Model):
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    roll_number = models.CharField(max_length=50, unique=True)
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='contestants')
    points = models.IntegerField(default=0)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.roll_number})"

    class Meta:
        ordering = ['-points', 'name']


class PointTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('add', 'Add Points'),
        ('deduct', 'Deduct Points'),
    ]

    contestant = models.ForeignKey(
        Contestant, on_delete=models.CASCADE, related_name='transactions'
    )
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    points = models.PositiveIntegerField()
    reason = models.CharField(max_length=300, blank=True)
    performed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='point_transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} {self.points} pts for {self.contestant.name}"
