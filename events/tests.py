import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from .models import Event, Round, Contestant, PointTransaction


class ModelTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(name="Business Arena", description="Test event", date=datetime.date.today())
        self.round_head = User.objects.create_user(username="roundhead1", password="testpass123")
        self.round = Round.objects.create(event=self.event, name="Round 1", round_head=self.round_head)
        self.contestant = Contestant.objects.create(
            name="Alice", phone_number="03001234567", roll_number="BSCS-F21-001", round=self.round
        )

    def test_event_str(self):
        self.assertEqual(str(self.event), "Business Arena")

    def test_round_str(self):
        self.assertEqual(str(self.round), "Business Arena - Round 1")

    def test_contestant_str(self):
        self.assertEqual(str(self.contestant), "Alice (BSCS-F21-001)")

    def test_contestant_default_points(self):
        self.assertEqual(self.contestant.points, 0)

    def test_point_transaction_str(self):
        pt = PointTransaction.objects.create(
            contestant=self.contestant, transaction_type="add", points=10, performed_by=self.round_head
        )
        self.assertIn("add", str(pt))
        self.assertIn("Alice", str(pt))


class RegistrationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.event = Event.objects.create(name="Arena", description="", date=datetime.date.today())
        self.round = Round.objects.create(event=self.event, name="Prelims")

    def test_register_contestant(self):
        data = {
            "name": "Bob",
            "phone_number": "03001234567",
            "roll_number": "BSCS-F21-002",
            "round": self.round.id,
        }
        res = self.client.post("/api/register/", data, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Contestant.objects.count(), 1)

    def test_register_duplicate_roll_number(self):
        Contestant.objects.create(name="Bob", phone_number="0300", roll_number="BSCS-001", round=self.round)
        data = {"name": "Carol", "phone_number": "0301", "roll_number": "BSCS-001", "round": self.round.id}
        res = self.client.post("/api/register/", data, format="json")
        self.assertEqual(res.status_code, 400)

    def test_register_missing_fields(self):
        res = self.client.post("/api/register/", {}, format="json")
        self.assertEqual(res.status_code, 400)


class PointsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.event = Event.objects.create(name="Arena", description="", date=datetime.date.today())
        self.round_head = User.objects.create_user(username="rh", password="testpass123")
        self.round = Round.objects.create(event=self.event, name="Finals", round_head=self.round_head)
        self.contestant = Contestant.objects.create(
            name="Dave", phone_number="03001234567", roll_number="BSCS-002", round=self.round
        )

    def test_add_points_as_round_head(self):
        self.client.login(username="rh", password="testpass123")
        data = {"contestant": self.contestant.id, "transaction_type": "add", "points": 20}
        res = self.client.post("/api/points/", data, format="json")
        self.assertEqual(res.status_code, 201)
        self.contestant.refresh_from_db()
        self.assertEqual(self.contestant.points, 20)

    def test_deduct_points(self):
        self.contestant.points = 30
        self.contestant.save()
        self.client.login(username="rh", password="testpass123")
        data = {"contestant": self.contestant.id, "transaction_type": "deduct", "points": 10}
        res = self.client.post("/api/points/", data, format="json")
        self.assertEqual(res.status_code, 201)
        self.contestant.refresh_from_db()
        self.assertEqual(self.contestant.points, 20)

    def test_deduct_points_cannot_go_below_zero(self):
        self.contestant.points = 5
        self.contestant.save()
        self.client.login(username="rh", password="testpass123")
        data = {"contestant": self.contestant.id, "transaction_type": "deduct", "points": 100}
        res = self.client.post("/api/points/", data, format="json")
        self.assertEqual(res.status_code, 201)
        self.contestant.refresh_from_db()
        self.assertEqual(self.contestant.points, 0)

    def test_unauthenticated_cannot_update_points(self):
        data = {"contestant": self.contestant.id, "transaction_type": "add", "points": 10}
        res = self.client.post("/api/points/", data, format="json")
        self.assertEqual(res.status_code, 403)

    def test_non_round_head_cannot_update_points(self):
        other = User.objects.create_user(username="other", password="testpass123")
        self.client.login(username="other", password="testpass123")
        data = {"contestant": self.contestant.id, "transaction_type": "add", "points": 10}
        res = self.client.post("/api/points/", data, format="json")
        self.assertEqual(res.status_code, 403)


class LeaderboardAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.event = Event.objects.create(name="Arena", description="", date=datetime.date.today())
        self.round = Round.objects.create(event=self.event, name="Round A")
        Contestant.objects.create(name="Eve", phone_number="0300", roll_number="R1", round=self.round, points=50)
        Contestant.objects.create(name="Frank", phone_number="0301", roll_number="R2", round=self.round, points=80)

    def test_leaderboard_returns_data(self):
        res = self.client.get("/api/leaderboard/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        contestants = res.data[0]['contestants']
        self.assertEqual(contestants[0]['name'], "Frank")  # highest points first

    def test_leaderboard_filter_by_round(self):
        other_round = Round.objects.create(event=self.event, name="Round B")
        Contestant.objects.create(name="Grace", phone_number="0302", roll_number="R3", round=other_round, points=100)
        res = self.client.get(f"/api/leaderboard/?round={self.round.id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['round_name'], "Round A")


class FrontendViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.event = Event.objects.create(name="Arena", description="", date=datetime.date.today())
        self.round_head = User.objects.create_user(username="rh", password="testpass123")
        self.round = Round.objects.create(event=self.event, name="Round 1", round_head=self.round_head)

    def test_introduction_page(self):
        res = self.client.get(reverse('introduction'))
        self.assertEqual(res.status_code, 200)

    def test_register_page(self):
        res = self.client.get(reverse('register'))
        self.assertEqual(res.status_code, 200)

    def test_leaderboard_page(self):
        res = self.client.get(reverse('leaderboard'))
        self.assertEqual(res.status_code, 200)

    def test_dashboard_requires_login(self):
        res = self.client.get(reverse('dashboard'))
        self.assertEqual(res.status_code, 302)  # redirect to login

    def test_dashboard_accessible_to_round_head(self):
        self.client.login(username="rh", password="testpass123")
        res = self.client.get(reverse('dashboard'))
        self.assertEqual(res.status_code, 200)
