from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import transaction as db_transaction
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Event, Round, Contestant, PointTransaction
from .serializers import (
    EventSerializer,
    RoundSerializer,
    RoundListSerializer,
    ContestantSerializer,
    PointTransactionSerializer,
    RegistrationSerializer,
)
from .permissions import IsRoundHead


# ---------------------------------------------------------------------------
# Template views
# ---------------------------------------------------------------------------

def introduction(request):
    """Introduction / landing page."""
    return render(request, 'events/introduction.html')


def register(request):
    """Public contestant registration page."""
    rounds = Round.objects.select_related('event').order_by('event__name', 'name')
    return render(request, 'events/register.html', {'rounds': rounds})


def leaderboard(request):
    """Live leaderboard page — only shows rounds the round head has made visible."""
    rounds = (
        Round.objects
        .filter(leaderboard_visible=True)
        .prefetch_related('contestants')
        .select_related('event')
        .order_by('event__name', 'name')
    )
    return render(request, 'events/leaderboard.html', {'rounds': rounds})


@login_required
def round_head_dashboard(request):
    """Round head admin dashboard."""
    if request.user.is_superuser:
        managed_rounds = Round.objects.prefetch_related('contestants').select_related('event')
    else:
        managed_rounds = Round.objects.filter(round_head=request.user).prefetch_related('contestants').select_related('event')
        if not managed_rounds.exists():
            return render(request, 'events/no_access.html', status=403)
    return render(request, 'events/dashboard.html', {'managed_rounds': managed_rounds})


@login_required
@require_POST
def toggle_leaderboard(request, round_id):
    """Toggle leaderboard visibility for a round. Only the round head or superuser can do this."""
    if request.user.is_superuser:
        rnd = get_object_or_404(Round, pk=round_id)
    else:
        rnd = get_object_or_404(Round, pk=round_id, round_head=request.user)

    rnd.leaderboard_visible = not rnd.leaderboard_visible
    rnd.save(update_fields=['leaderboard_visible'])
    return JsonResponse({'visible': rnd.leaderboard_visible})


# ---------------------------------------------------------------------------
# REST API ViewSets
# ---------------------------------------------------------------------------

class EventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Event.objects.prefetch_related('rounds').order_by('date')
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]


class RoundViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Round.objects.select_related('event', 'round_head').order_by('event__name', 'name')
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RoundSerializer
        return RoundListSerializer


class ContestantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Contestant.objects.select_related('round').order_by('-points', 'name')
    serializer_class = ContestantSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        round_id = self.request.query_params.get('round')
        if round_id:
            qs = qs.filter(round_id=round_id)
        return qs


class RegistrationViewSet(viewsets.GenericViewSet):
    """Public endpoint to register a contestant."""
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Registration successful!', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PointTransactionViewSet(viewsets.GenericViewSet):
    """Endpoint for round heads to add/deduct points."""
    serializer_class = PointTransactionSerializer
    permission_classes = [IsRoundHead]

    def _get_contestant_for_round_head(self, contestant_id, user):
        qs = Contestant.objects.select_related('round')
        if not user.is_superuser:
            qs = qs.filter(round__round_head=user)
        return get_object_or_404(qs, pk=contestant_id)

    def create(self, request):
        contestant_id = request.data.get('contestant')
        transaction_type = request.data.get('transaction_type')
        points = request.data.get('points')
        reason = request.data.get('reason', '')

        if not all([contestant_id, transaction_type, points]):
            return Response({'error': 'contestant, transaction_type, and points are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            points = int(points)
            if points <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response({'error': 'Points must be a positive integer.'}, status=status.HTTP_400_BAD_REQUEST)

        if transaction_type not in ('add', 'deduct'):
            return Response({'error': 'transaction_type must be "add" or "deduct".'}, status=status.HTTP_400_BAD_REQUEST)

        contestant = self._get_contestant_for_round_head(contestant_id, request.user)

        with db_transaction.atomic():
            if transaction_type == 'add':
                contestant.points += points
            else:
                contestant.points = max(0, contestant.points - points)
            contestant.save()

            pt = PointTransaction.objects.create(
                contestant=contestant,
                transaction_type=transaction_type,
                points=points,
                reason=reason,
                performed_by=request.user,
            )

        serializer = PointTransactionSerializer(pt)
        return Response({
            'message': 'Points updated successfully.',
            'transaction': serializer.data,
            'new_total': contestant.points,
        }, status=status.HTTP_201_CREATED)


class LeaderboardViewSet(viewsets.GenericViewSet):
    """API endpoint to fetch leaderboard data — only visible rounds."""
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        round_id = request.query_params.get('round')
        rounds_qs = (
            Round.objects
            .filter(leaderboard_visible=True)
            .select_related('event')
            .prefetch_related('contestants')
            .order_by('event__name', 'name')
        )
        if round_id:
            rounds_qs = rounds_qs.filter(pk=round_id)

        data = []
        for rnd in rounds_qs:
            contestants = list(rnd.contestants.order_by('-points', 'name').values('id', 'name', 'roll_number', 'points'))
            data.append({
                'round_id': rnd.id,
                'round_name': rnd.name,
                'event_name': rnd.event.name,
                'contestants': contestants,
            })
        return Response(data)
