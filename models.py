from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# Association table for subscriber tags (many-to-many)
subscriber_tags = db.Table(
    "subscriber_tags",
    db.Column(
        "subscriber_id", db.Integer, db.ForeignKey("subscriber.id"), primary_key=True
    ),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class Subscriber(db.Model):
    """A person subscribed to receive emails."""

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), default="")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    tags = db.relationship("Tag", secondary=subscriber_tags, backref="subscribers")
    email_logs = db.relationship("EmailLog", backref="subscriber", lazy=True)

    def __repr__(self):
        return f"<Subscriber {self.email}>"

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "department": self.department,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tags": [tag.name for tag in self.tags],
        }


class Tag(db.Model):
    """Tags for segmenting subscribers (e.g. 'engineering', 'freshman')."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"<Tag {self.name}>"


class Campaign(db.Model):
    """An email campaign targeting a group of subscribers."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body_html = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="draft")  # draft, scheduled, sent
    scheduled_at = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    target_tag = db.Column(db.String(50), default="")  # optional tag filter

    email_logs = db.relationship("EmailLog", backref="campaign", lazy=True)

    def __repr__(self):
        return f"<Campaign {self.name}>"

    @property
    def total_sent(self):
        return len([log for log in self.email_logs if log.status == "sent"])

    @property
    def total_opened(self):
        return len([log for log in self.email_logs if log.opened])

    @property
    def open_rate(self):
        if self.total_sent == 0:
            return 0
        return round((self.total_opened / self.total_sent) * 100, 1)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "subject": self.subject,
            "status": self.status,
            "scheduled_at": (
                self.scheduled_at.isoformat() if self.scheduled_at else None
            ),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "target_tag": self.target_tag,
            "total_sent": self.total_sent,
            "total_opened": self.total_opened,
            "open_rate": self.open_rate,
        }


class EmailLog(db.Model):
    """Tracks individual email deliveries and engagement."""

    id = db.Column(db.Integer, primary_key=True)
    subscriber_id = db.Column(
        db.Integer, db.ForeignKey("subscriber.id"), nullable=False
    )
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaign.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending, sent, failed
    opened = db.Column(db.Boolean, default=False)
    opened_at = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<EmailLog {self.id} subscriber={self.subscriber_id}>"
