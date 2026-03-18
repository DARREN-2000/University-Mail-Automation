"""University Event Email Marketing Automation System.

A Flask web application for managing email campaigns, subscriber lists,
and automated communications for university events and announcements.
"""

import csv
import io
import logging
import os
from datetime import datetime

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from config import Config
from email_service import get_dashboard_stats, mail, record_open, send_campaign, send_welcome_email
from models import Campaign, EmailLog, Subscriber, Tag, db

logging.basicConfig(level=logging.INFO)


def get_server_config():
    """Get host/port for local and hosted environments."""
    return {
        "host": os.environ.get("HOST", "0.0.0.0"),
        "port": int(os.environ.get("PORT", 5000)),
    }


def create_app(config_class=Config):
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    mail.init_app(app)

    with app.app_context():
        db.create_all()

    register_routes(app)
    return app


def register_routes(app):
    """Register all application routes."""

    # ── Dashboard ──────────────────────────────────────────────────────

    @app.route("/")
    def dashboard():
        stats = get_dashboard_stats()
        recent_campaigns = (
            Campaign.query.filter(Campaign.name != "__welcome__")
            .order_by(Campaign.created_at.desc())
            .limit(5)
            .all()
        )
        return render_template(
            "dashboard.html", stats=stats, recent_campaigns=recent_campaigns
        )

    # ── Subscribers ────────────────────────────────────────────────────

    @app.route("/subscribers")
    def subscribers():
        page = request.args.get("page", 1, type=int)
        tag_filter = request.args.get("tag", "")
        query = Subscriber.query

        if tag_filter:
            tag = Tag.query.filter_by(name=tag_filter).first()
            if tag:
                query = query.filter(Subscriber.tags.contains(tag))

        pagination = query.order_by(Subscriber.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        all_tags = Tag.query.order_by(Tag.name).all()
        return render_template(
            "subscribers.html",
            subscribers=pagination.items,
            pagination=pagination,
            tags=all_tags,
            current_tag=tag_filter,
        )

    @app.route("/subscribers/add", methods=["POST"])
    def add_subscriber():
        email = request.form.get("email", "").strip()
        name = request.form.get("name", "").strip()
        department = request.form.get("department", "").strip()
        tag_names = request.form.get("tags", "").strip()

        if not email or not name:
            flash("Email and name are required.", "error")
            return redirect(url_for("subscribers"))

        if Subscriber.query.filter_by(email=email).first():
            flash("A subscriber with this email already exists.", "error")
            return redirect(url_for("subscribers"))

        subscriber = Subscriber(email=email, name=name, department=department)

        db.session.add(subscriber)

        # Handle tags
        if tag_names:
            for tag_name in tag_names.split(","):
                tag_name = tag_name.strip().lower()
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    subscriber.tags.append(tag)
        db.session.commit()

        flash(f"Subscriber '{name}' added successfully!", "success")

        # Send welcome email asynchronously
        send_welcome_email(app, subscriber.id)

        return redirect(url_for("subscribers"))

    @app.route("/subscribers/<int:subscriber_id>/toggle", methods=["POST"])
    def toggle_subscriber(subscriber_id):
        subscriber = db.session.get(Subscriber, subscriber_id)
        if subscriber:
            subscriber.is_active = not subscriber.is_active
            db.session.commit()
            status = "activated" if subscriber.is_active else "deactivated"
            flash(f"Subscriber {status}.", "success")
        return redirect(url_for("subscribers"))

    @app.route("/subscribers/import", methods=["POST"])
    def import_subscribers():
        file = request.files.get("csv_file")
        if not file or not file.filename.endswith(".csv"):
            flash("Please upload a valid CSV file.", "error")
            return redirect(url_for("subscribers"))

        stream = io.StringIO(file.stream.read().decode("utf-8"))
        reader = csv.DictReader(stream)

        added = 0
        skipped = 0
        for row in reader:
            email = row.get("email", "").strip()
            name = row.get("name", "").strip()
            department = row.get("department", "").strip()

            if not email or not name:
                skipped += 1
                continue

            if Subscriber.query.filter_by(email=email).first():
                skipped += 1
                continue

            subscriber = Subscriber(
                email=email, name=name, department=department
            )
            db.session.add(subscriber)
            added += 1

        db.session.commit()
        flash(f"Imported {added} subscribers ({skipped} skipped).", "success")
        return redirect(url_for("subscribers"))

    @app.route("/subscribers/export")
    def export_subscribers():
        subscribers_list = Subscriber.query.all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["name", "email", "department", "is_active", "tags"])
        for sub in subscribers_list:
            tags = ", ".join(t.name for t in sub.tags)
            writer.writerow(
                [sub.name, sub.email, sub.department, sub.is_active, tags]
            )

        mem = io.BytesIO()
        mem.write(output.getvalue().encode("utf-8"))
        mem.seek(0)
        return send_file(
            mem,
            mimetype="text/csv",
            as_attachment=True,
            download_name="subscribers.csv",
        )

    # ── Campaigns ──────────────────────────────────────────────────────

    @app.route("/campaigns")
    def campaigns():
        all_campaigns = (
            Campaign.query.filter(Campaign.name != "__welcome__")
            .order_by(Campaign.created_at.desc())
            .all()
        )
        return render_template("campaigns.html", campaigns=all_campaigns)

    @app.route("/campaigns/create", methods=["GET", "POST"])
    def create_campaign():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            subject = request.form.get("subject", "").strip()
            body_html = request.form.get("body_html", "").strip()
            target_tag = request.form.get("target_tag", "").strip()
            scheduled_at_str = request.form.get("scheduled_at", "").strip()

            if not name or not subject or not body_html:
                flash("Name, subject, and body are required.", "error")
                return redirect(url_for("create_campaign"))

            campaign = Campaign(
                name=name,
                subject=subject,
                body_html=body_html,
                target_tag=target_tag,
            )

            if scheduled_at_str:
                try:
                    campaign.scheduled_at = datetime.strptime(
                        scheduled_at_str, "%Y-%m-%dT%H:%M"
                    )
                    campaign.status = "scheduled"
                except ValueError:
                    flash("Invalid date format.", "error")
                    return redirect(url_for("create_campaign"))

            db.session.add(campaign)
            db.session.commit()

            flash(f"Campaign '{name}' created!", "success")
            return redirect(url_for("campaigns"))

        tags = Tag.query.order_by(Tag.name).all()
        return render_template("create_campaign.html", tags=tags)

    @app.route("/campaigns/<int:campaign_id>/send", methods=["POST"])
    def send_campaign_route(campaign_id):
        campaign = db.session.get(Campaign, campaign_id)
        if not campaign:
            flash("Campaign not found.", "error")
            return redirect(url_for("campaigns"))

        if campaign.status == "sent":
            flash("Campaign has already been sent.", "error")
            return redirect(url_for("campaigns"))

        count = send_campaign(app, campaign_id)
        flash(f"Campaign sent to {count} subscribers!", "success")
        return redirect(url_for("campaigns"))

    @app.route("/campaigns/<int:campaign_id>")
    def campaign_detail(campaign_id):
        campaign = db.session.get(Campaign, campaign_id)
        if not campaign:
            flash("Campaign not found.", "error")
            return redirect(url_for("campaigns"))

        logs = (
            EmailLog.query.filter_by(campaign_id=campaign_id)
            .order_by(EmailLog.sent_at.desc())
            .all()
        )
        return render_template(
            "campaign_detail.html", campaign=campaign, logs=logs
        )

    # ── Tracking ───────────────────────────────────────────────────────

    @app.route("/track/<int:log_id>/open.png")
    def track_open(log_id):
        record_open(log_id)
        # Return a 1x1 transparent pixel
        pixel = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00"
            b"\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00"
            b"\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02"
            b"\x44\x01\x00\x3b"
        )
        return pixel, 200, {"Content-Type": "image/gif"}

    # ── API endpoints (for programmatic access) ────────────────────────

    @app.route("/api/stats")
    def api_stats():
        return jsonify(get_dashboard_stats())

    @app.route("/api/subscribers")
    def api_subscribers():
        subs = Subscriber.query.filter_by(is_active=True).all()
        return jsonify([s.to_dict() for s in subs])

    @app.route("/api/campaigns")
    def api_campaigns():
        camps = Campaign.query.filter(Campaign.name != "__welcome__").all()
        return jsonify([c.to_dict() for c in camps])


if __name__ == "__main__":
    app = create_app()
    app.run(**get_server_config())
