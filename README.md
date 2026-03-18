# UniMail — University Email Marketing Automation

A practical email marketing automation system built for university use cases. Manage subscriber lists, create and send email campaigns, track engagement, and automate communications for campus events and announcements.

## Features

- **Subscriber Management** — Add, import (CSV), export, activate/deactivate subscribers
- **Tag-Based Segmentation** — Organize subscribers by department, year, interest (e.g. `engineering`, `freshman`)
- **Campaign Builder** — Create email campaigns with HTML content, target specific segments, and schedule sends
- **Automated Welcome Emails** — New subscribers automatically receive a welcome message
- **Open Tracking** — Embedded tracking pixel records when recipients open emails
- **Dashboard & Analytics** — View total subscribers, campaigns sent, open rates at a glance
- **REST API** — Programmatic access to stats, subscribers, and campaigns (`/api/stats`, `/api/subscribers`, `/api/campaigns`)
- **CSV Import/Export** — Bulk manage subscriber lists via CSV files

## Tech Stack

| Layer       | Technology       |
|-------------|------------------|
| Backend     | Python / Flask   |
| Database    | SQLite (via SQLAlchemy) |
| Email       | Flask-Mail (SMTP)|
| Scheduling  | APScheduler      |
| Frontend    | Jinja2 Templates + CSS |
| Testing     | pytest           |

## Getting Started

### Prerequisites

- Python 3.10+

### Installation

```bash
# Clone the repository
git clone https://github.com/DARREN-2000/University-Mail-Automation.git
cd University-Mail-Automation

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file (optional) to configure email settings:

```env
SECRET_KEY=your-secret-key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
DATABASE_URL=sqlite:///marketing.db
BASE_URL=http://localhost:5000
```

You can copy `.env.example` and edit it:

```bash
cp .env.example .env
```

### Run the Application

```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

## Quick Demo (No SMTP Required)

If you want to demo the UI quickly without configuring email credentials:

1. Start the app with `python app.py`
2. Open `http://localhost:5000`
3. Add subscribers from the **Subscribers** page
4. Create a campaign from **Campaigns → Create Campaign**
5. Send the campaign (email sends will fail without SMTP, but campaign flow and analytics UI remain demoable)

### Run Tests

```bash
python -m pytest tests/ -v
```

## Free Deployment (Render)

This repository includes `render.yaml` for a free Render web service setup.

1. Push your code to GitHub
2. In Render, create a new **Blueprint** and select this repository
3. Render reads `render.yaml` and provisions the service on the free plan
4. Set `BASE_URL` to your Render URL (for tracking links), for example:
   - `https://university-mail-automation.onrender.com`

The app binds to `PORT` automatically and can also run locally with:

```bash
python app.py
```

## Project Structure

```
├── app.py              # Flask application and routes
├── models.py           # Database models (Subscriber, Campaign, EmailLog, Tag)
├── email_service.py    # Email sending and tracking logic
├── config.py           # Application configuration
├── requirements.txt    # Python dependencies
├── templates/          # Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── subscribers.html
│   ├── campaigns.html
│   ├── create_campaign.html
│   └── campaign_detail.html
├── static/
│   └── style.css       # Application styles
└── tests/
    └── test_app.py     # Unit and integration tests
```

## Use Case Example

A university's Student Activities Office uses UniMail to:

1. **Import** the student mailing list via CSV
2. **Tag** subscribers by department (`cs`, `engineering`, `business`)
3. **Create a campaign** announcing the Spring Career Fair, targeting only `engineering` students
4. **Send** the campaign — each student receives a personalized email
5. **Track** which students opened the email via the dashboard
6. **Send follow-up** reminders to boost attendance
