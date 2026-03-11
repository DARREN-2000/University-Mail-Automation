"""Email sending and tracking service."""

import logging
from datetime import datetime, timezone

from flask import url_for
from flask_mail import Mail, Message

from models import Campaign, EmailLog, Subscriber, Tag, db

mail = Mail()
logger = logging.getLogger(__name__)


def send_campaign(app, campaign_id):
    """Send a campaign to all targeted active subscribers."""
    with app.app_context():
        campaign = db.session.get(Campaign, campaign_id)
        if not campaign:
            logger.error("Campaign %s not found", campaign_id)
            return 0

        # Build subscriber query
        query = Subscriber.query.filter_by(is_active=True)

        if campaign.target_tag:
            tag = Tag.query.filter_by(name=campaign.target_tag).first()
            if tag:
                query = query.filter(Subscriber.tags.contains(tag))

        subscribers = query.all()
        sent_count = 0

        for subscriber in subscribers:
            # Skip if already sent to this subscriber for this campaign
            existing = EmailLog.query.filter_by(
                subscriber_id=subscriber.id,
                campaign_id=campaign.id,
                status="sent",
            ).first()
            if existing:
                continue

            success = _send_email(
                app, subscriber, campaign.subject, campaign.body_html, campaign.id
            )
            if success:
                sent_count += 1

        campaign.status = "sent"
        campaign.sent_at = datetime.now(timezone.utc)
        db.session.commit()

        logger.info(
            "Campaign '%s' sent to %d subscribers", campaign.name, sent_count
        )
        return sent_count


def send_welcome_email(app, subscriber_id):
    """Send an automated welcome email to a new subscriber."""
    with app.app_context():
        subscriber = db.session.get(Subscriber, subscriber_id)
        if not subscriber:
            return False

        subject = "Welcome to University Updates!"
        body = f"""
        <html>
        <body>
            <h2>Welcome, {subscriber.name}!</h2>
            <p>Thank you for subscribing to University Updates.</p>
            <p>You'll receive notifications about:</p>
            <ul>
                <li>Upcoming events and workshops</li>
                <li>Important announcements</li>
                <li>Department-specific news</li>
            </ul>
            <p>Stay connected!</p>
            <p><em>University Marketing Team</em></p>
        </body>
        </html>
        """

        # Create a special "welcome" campaign if it doesn't exist
        welcome_campaign = Campaign.query.filter_by(name="__welcome__").first()
        if not welcome_campaign:
            welcome_campaign = Campaign(
                name="__welcome__",
                subject=subject,
                body_html=body,
                status="sent",
            )
            db.session.add(welcome_campaign)
            db.session.commit()

        return _send_email(app, subscriber, subject, body, welcome_campaign.id)


def _send_email(app, subscriber, subject, body_html, campaign_id):
    """Send a single email and log the result."""
    email_log = EmailLog(
        subscriber_id=subscriber.id,
        campaign_id=campaign_id,
        status="pending",
    )
    db.session.add(email_log)
    db.session.commit()

    try:
        # Add tracking pixel
        tracking_url = url_for(
            "track_open", log_id=email_log.id, _external=True
        )
        tracking_pixel = (
            f'<img src="{tracking_url}" width="1" height="1" alt="" />'
        )
        body_with_tracking = body_html + tracking_pixel

        msg = Message(
            subject=subject,
            recipients=[subscriber.email],
            html=body_with_tracking,
        )
        mail.send(msg)

        email_log.status = "sent"
        email_log.sent_at = datetime.now(timezone.utc)
        db.session.commit()
        return True

    except Exception as e:
        logger.error("Failed to send email to %s: %s", subscriber.email, e)
        email_log.status = "failed"
        db.session.commit()
        return False


def record_open(log_id):
    """Record that an email was opened (via tracking pixel)."""
    email_log = db.session.get(EmailLog, log_id)
    if email_log and not email_log.opened:
        email_log.opened = True
        email_log.opened_at = datetime.now(timezone.utc)
        db.session.commit()
        return True
    return False


def get_dashboard_stats():
    """Return aggregate statistics for the dashboard."""
    total_subscribers = Subscriber.query.filter_by(is_active=True).count()
    total_campaigns = Campaign.query.filter(Campaign.name != "__welcome__").count()
    total_sent = EmailLog.query.filter_by(status="sent").count()
    total_opened = EmailLog.query.filter_by(opened=True).count()

    open_rate = 0
    if total_sent > 0:
        open_rate = round((total_opened / total_sent) * 100, 1)

    return {
        "total_subscribers": total_subscribers,
        "total_campaigns": total_campaigns,
        "total_emails_sent": total_sent,
        "total_opens": total_opened,
        "open_rate": open_rate,
    }
