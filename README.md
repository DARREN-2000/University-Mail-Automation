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
git clone https://github.com/DARREN-2000/to.git
cd to

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
```

### Run the Application

```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

### Run Tests

```bash
python -m pytest tests/ -v
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
