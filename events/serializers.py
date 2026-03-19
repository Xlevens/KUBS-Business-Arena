from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Event, Round, Contestant, PointTransaction


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class ContestantSerializer(serializers.ModelSerializer):
    round_name = serializers.CharField(source='round.name', read_only=True)

    class Meta:
        model = Contestant
        fields = ['id', 'name', 'phone_number', 'roll_number', 'round', 'round_name', 'points', 'registered_at']
        read_only_fields = ['points', 'registered_at']


class RoundSerializer(serializers.ModelSerializer):
    round_head = UserSerializer(read_only=True)
    contestants = ContestantSerializer(many=True, read_only=True)

    class Meta:
        model = Round
        fields = ['id', 'event', 'name', 'description', 'round_head', 'contestants', 'created_at']


class RoundListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing rounds (no nested contestants)."""
    round_head_username = serializers.CharField(source='round_head.username', read_only=True)

    class Meta:
        model = Round
        fields = ['id', 'event', 'name', 'description', 'round_head_username', 'created_at']


class EventSerializer(serializers.ModelSerializer):
    rounds = RoundListSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'name', 'description', 'date', 'rounds', 'created_at']


class PointTransactionSerializer(serializers.ModelSerializer):
    performed_by = UserSerializer(read_only=True)
    contestant_name = serializers.CharField(source='contestant.name', read_only=True)

    class Meta:
        model = PointTransaction
        fields = ['id', 'contestant', 'contestant_name', 'transaction_type', 'points', 'reason', 'performed_by', 'created_at']
        read_only_fields = ['performed_by', 'created_at']


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer used for the public registration form."""

    class Meta:
        model = Contestant
        fields = ['name', 'phone_number', 'roll_number', 'round']

    def validate_phone_number(self, value):
        cleaned = ''.join(filter(str.isdigit, value.replace('+', '')))
        if len(cleaned) < 7:
            raise serializers.ValidationError("Enter a valid phone number.")
        return value
