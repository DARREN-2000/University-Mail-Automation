"""Tests for the UniMail application."""

import csv
import io

import pytest

from app import create_app, get_server_config
from config import TestConfig
from models import Campaign, EmailLog, Subscriber, Tag, db


@pytest.fixture
def app():
    """Create and configure a test application instance."""
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def sample_subscriber(app):
    """Create a sample subscriber."""
    with app.app_context():
        sub = Subscriber(
            name="Alice Johnson",
            email="alice@university.edu",
            department="Computer Science",
        )
        db.session.add(sub)
        db.session.commit()
        return sub.id


@pytest.fixture
def sample_campaign(app):
    """Create a sample campaign."""
    with app.app_context():
        campaign = Campaign(
            name="Spring Event",
            subject="Join our Spring Event!",
            body_html="<h1>Spring Event</h1><p>You're invited!</p>",
        )
        db.session.add(campaign)
        db.session.commit()
        return campaign.id


# ── Model Tests ────────────────────────────────────────────────────────


class TestSubscriberModel:
    def test_create_subscriber(self, app):
        with app.app_context():
            sub = Subscriber(
                name="Bob Smith",
                email="bob@university.edu",
                department="Physics",
            )
            db.session.add(sub)
            db.session.commit()

            assert sub.id is not None
            assert sub.is_active is True
            assert sub.email == "bob@university.edu"

    def test_subscriber_to_dict(self, app):
        with app.app_context():
            sub = Subscriber(
                name="Charlie", email="charlie@uni.edu", department="Math"
            )
            db.session.add(sub)
            db.session.commit()

            data = sub.to_dict()
            assert data["name"] == "Charlie"
            assert data["email"] == "charlie@uni.edu"
            assert data["is_active"] is True

    def test_subscriber_with_tags(self, app):
        with app.app_context():
            tag = Tag(name="engineering")
            sub = Subscriber(name="Diana", email="diana@uni.edu")
            sub.tags.append(tag)
            db.session.add(sub)
            db.session.commit()

            assert len(sub.tags) == 1
            assert sub.tags[0].name == "engineering"

    def test_unique_email_constraint(self, app):
        with app.app_context():
            sub1 = Subscriber(name="Eve", email="eve@uni.edu")
            sub2 = Subscriber(name="Eve2", email="eve@uni.edu")
            db.session.add(sub1)
            db.session.commit()
            db.session.add(sub2)
            with pytest.raises(Exception):
                db.session.commit()


class TestCampaignModel:
    def test_create_campaign(self, app):
        with app.app_context():
            campaign = Campaign(
                name="Test Campaign",
                subject="Test Subject",
                body_html="<p>Hello</p>",
            )
            db.session.add(campaign)
            db.session.commit()

            assert campaign.id is not None
            assert campaign.status == "draft"

    def test_campaign_stats(self, app):
        with app.app_context():
            campaign = Campaign(
                name="Stats Test",
                subject="Stats",
                body_html="<p>Test</p>",
            )
            sub = Subscriber(name="Test", email="test@uni.edu")
            db.session.add_all([campaign, sub])
            db.session.commit()

            log = EmailLog(
                subscriber_id=sub.id,
                campaign_id=campaign.id,
                status="sent",
                opened=True,
            )
            db.session.add(log)
            db.session.commit()

            assert campaign.total_sent == 1
            assert campaign.total_opened == 1
            assert campaign.open_rate == 100.0

    def test_campaign_zero_open_rate(self, app):
        with app.app_context():
            campaign = Campaign(
                name="Empty",
                subject="Empty",
                body_html="<p>Test</p>",
            )
            db.session.add(campaign)
            db.session.commit()
            assert campaign.open_rate == 0


# ── Route Tests ────────────────────────────────────────────────────────


class TestDashboard:
    def test_dashboard_loads(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert b"Dashboard" in response.data

    def test_dashboard_shows_stats(self, client):
        response = client.get("/")
        assert b"Active Subscribers" in response.data
        assert b"Campaigns" in response.data


class TestSubscriberRoutes:
    def test_subscribers_page_loads(self, client):
        response = client.get("/subscribers")
        assert response.status_code == 200
        assert b"Subscribers" in response.data

    def test_add_subscriber(self, client):
        response = client.post(
            "/subscribers/add",
            data={
                "name": "Frank Miller",
                "email": "frank@university.edu",
                "department": "Biology",
                "tags": "biology, freshman",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Frank Miller" in response.data

    def test_add_subscriber_missing_fields(self, client):
        response = client.post(
            "/subscribers/add",
            data={"name": "", "email": ""},
            follow_redirects=True,
        )
        assert b"required" in response.data

    def test_add_duplicate_subscriber(self, client, sample_subscriber):
        response = client.post(
            "/subscribers/add",
            data={
                "name": "Alice Clone",
                "email": "alice@university.edu",
            },
            follow_redirects=True,
        )
        assert b"already exists" in response.data

    def test_toggle_subscriber(self, client, app, sample_subscriber):
        response = client.post(
            f"/subscribers/{sample_subscriber}/toggle",
            follow_redirects=True,
        )
        assert response.status_code == 200

        with app.app_context():
            sub = db.session.get(Subscriber, sample_subscriber)
            assert sub.is_active is False

    def test_import_csv(self, client):
        csv_data = "name,email,department\nGrace,grace@uni.edu,CS\nHeidi,heidi@uni.edu,Math"
        data = {
            "csv_file": (io.BytesIO(csv_data.encode()), "subscribers.csv"),
        }
        response = client.post(
            "/subscribers/import",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Imported 2" in response.data

    def test_export_csv(self, client, sample_subscriber):
        response = client.get("/subscribers/export")
        assert response.status_code == 200
        assert response.content_type == "text/csv; charset=utf-8"

    def test_subscriber_tag_filter(self, client, app):
        with app.app_context():
            tag = Tag(name="engineering")
            sub = Subscriber(name="Test", email="test@uni.edu")
            sub.tags.append(tag)
            db.session.add(sub)
            db.session.commit()

        response = client.get("/subscribers?tag=engineering")
        assert response.status_code == 200
        assert b"Test" in response.data


class TestCampaignRoutes:
    def test_campaigns_page_loads(self, client):
        response = client.get("/campaigns")
        assert response.status_code == 200
        assert b"Campaigns" in response.data

    def test_create_campaign_page_loads(self, client):
        response = client.get("/campaigns/create")
        assert response.status_code == 200
        assert b"Create Campaign" in response.data

    def test_create_campaign_post(self, client):
        response = client.post(
            "/campaigns/create",
            data={
                "name": "Fall Workshop",
                "subject": "Register for Fall Workshop",
                "body_html": "<h1>Fall Workshop</h1><p>Register now!</p>",
                "target_tag": "",
                "scheduled_at": "",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Fall Workshop" in response.data

    def test_create_campaign_with_schedule(self, client):
        response = client.post(
            "/campaigns/create",
            data={
                "name": "Scheduled Campaign",
                "subject": "Future Event",
                "body_html": "<p>Coming soon!</p>",
                "target_tag": "",
                "scheduled_at": "2025-12-25T10:00",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Scheduled Campaign" in response.data

    def test_create_campaign_missing_fields(self, client):
        response = client.post(
            "/campaigns/create",
            data={"name": "", "subject": "", "body_html": ""},
            follow_redirects=True,
        )
        assert b"required" in response.data

    def test_campaign_detail(self, client, sample_campaign):
        response = client.get(f"/campaigns/{sample_campaign}")
        assert response.status_code == 200
        assert b"Spring Event" in response.data

    def test_campaign_detail_not_found(self, client):
        response = client.get("/campaigns/999", follow_redirects=True)
        assert b"not found" in response.data

    def test_send_campaign(self, client, app, sample_campaign, sample_subscriber):
        response = client.post(
            f"/campaigns/{sample_campaign}/send",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Campaign sent" in response.data

    def test_send_already_sent_campaign(self, client, app, sample_campaign):
        with app.app_context():
            campaign = db.session.get(Campaign, sample_campaign)
            campaign.status = "sent"
            db.session.commit()

        response = client.post(
            f"/campaigns/{sample_campaign}/send",
            follow_redirects=True,
        )
        assert b"already been sent" in response.data


class TestTracking:
    def test_tracking_pixel(self, client, app, sample_subscriber, sample_campaign):
        with app.app_context():
            log = EmailLog(
                subscriber_id=sample_subscriber,
                campaign_id=sample_campaign,
                status="sent",
            )
            db.session.add(log)
            db.session.commit()
            log_id = log.id

        response = client.get(f"/track/{log_id}/open.png")
        assert response.status_code == 200
        assert response.content_type == "image/gif"

        with app.app_context():
            log = db.session.get(EmailLog, log_id)
            assert log.opened is True

    def test_tracking_pixel_nonexistent(self, client):
        response = client.get("/track/99999/open.png")
        assert response.status_code == 200  # Still returns pixel


class TestAPI:
    def test_api_stats(self, client):
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.get_json()
        assert "total_subscribers" in data
        assert "open_rate" in data

    def test_api_subscribers(self, client, sample_subscriber):
        response = client.get("/api/subscribers")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["email"] == "alice@university.edu"

    def test_api_campaigns(self, client, sample_campaign):
        response = client.get("/api/campaigns")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "Spring Event"


class TestServerConfig:
    def test_server_config_defaults(self, monkeypatch):
        monkeypatch.delenv("HOST", raising=False)
        monkeypatch.delenv("PORT", raising=False)

        config = get_server_config()
        assert config["host"] == "0.0.0.0"
        assert config["port"] == 5000

    def test_server_config_from_environment(self, monkeypatch):
        monkeypatch.setenv("HOST", "127.0.0.1")
        monkeypatch.setenv("PORT", "8080")

        config = get_server_config()
        assert config["host"] == "127.0.0.1"
        assert config["port"] == 8080
