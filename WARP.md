# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Architecture Overview

This is a Flask-based IT course management portal with Docker containerization and multi-environment deployment. The application manages course registrations, participant data, and course materials through a modular architecture.

### Core Architecture
- **Flask Web Application**: Main app in `web/app/app.py` with modular structure
- **Database**: MySQL 8.4 with SQLAlchemy ORM (`models.py`)
- **Multi-environment Docker Compose**: Base + Dev/Prod overrides
- **Content Management**: Dynamic course loading from JSON metadata and Markdown lessons
- **Admin System**: Token-based authentication for participant management

### Key Modules
- **Security**: Rate limiting, input sanitization, CSRF protection (`security.py`)
- **Monitoring**: Health checks, metrics endpoints (`monitoring.py`) 
- **Email Service**: Registration confirmations via Resend (`email_service.py`)
- **Content Loading**: Course metadata and lesson rendering (`utils/content_loader.py`, `utils/markdown_loader.py`)
- **Caching**: In-memory course caching with 10-minute TTL (`cache.py`)

## Development Commands

### Local Development
```bash
# Start development environment
docker compose -f compose.yml -f compose.dev.yml up --build

# Access points:
# - Webapp: http://127.0.0.1:5001
# - Adminer: http://127.0.0.1:8081

# Run tests
cd web && python -m pytest

# Check configuration
docker compose -f compose.yml -f compose.dev.yml config
```

### Production Deployment
```bash
# Deploy to production (Pi environment)
cd /home/pi/Dietipi-App
git pull
docker compose -f compose.yml -f compose.prod.yml up -d --build

# Verify deployment
docker compose -f compose.yml -f compose.prod.yml ps
docker compose -f compose.yml -f compose.prod.yml logs -n 20 webapp

# Add backup service (optional)
docker compose -f compose.yml -f compose.prod.yml -f compose.backup.yml up -d
```

### Database Operations
```bash
# Manual backup
docker compose exec backup /usr/local/bin/backup.sh

# Restore from backup
docker compose exec backup /usr/local/bin/restore.sh latest

# List available backups
docker compose exec backup /usr/local/bin/restore.sh
```

## Environment Configuration

### Required Environment Variables (.env in project root)
```
DB_ROOT_PASSWORD=<mysql_root_password>
DB_NAME=<database_name>
DB_USER=<database_user>
DB_PASSWORD=<database_password>
DATABASE_URL=mysql+pymysql://<user>:<password>@db:3306/<database>
ADMIN_TOKEN=<secret_admin_token>
CLOUDFLARE_TUNNEL_TOKEN=<cloudflare_tunnel_token>  # Production only
FLASK_DEBUG=0  # Production
```

The `.env.example` file provides template values. Never commit actual `.env` files.

## Key Development Patterns

### Admin Access
Admin routes require the `@require_admin` decorator and token authentication:
- URL parameter: `?admin=<ADMIN_TOKEN>`
- Header: `X-Admin-Token: <ADMIN_TOKEN>`

### Course Management
Courses are loaded dynamically from `web/app/content/meta/courses.json` with caching:
- Use `load_courses()` function for consistent course access
- Course visibility controlled by `visible` flag in JSON
- Course details can reference separate metadata files via `beschreibung_slug`

### Content Structure
- **Course Metadata**: `web/app/content/meta/*.json`
- **Lesson Content**: `web/app/content/unterlagen/durchfuehrungen/<course-id>/L<nn>/index.md`
- **Static Assets**: `web/app/static/` (images, PDFs, CSS)

### Database Models
- **Participant**: Main registration model with indexed fields for performance
- Uses SQLAlchemy with proper session management via `database.py` module
- Database health checks integrated into monitoring endpoints

### Testing Strategy
- Pytest with fixtures for app, database, and mocked external services
- Test coverage includes security functions, email validation, rate limiting
- Separate test configuration with mocked dependencies

### Security Features
- Rate limiting on registration endpoint (5 requests per 5 minutes)
- CSRF protection with Flask-WTF
- Input sanitization and validation
- Security headers (CSP, XSS protection, HSTS)
- Swiss-specific phone and email validation with typo detection

## Deployment Architecture

### Development (Mac/Local)
- Compose override exposes ports to localhost
- Flask development server with live reload
- Database accessible on localhost:3306

### Production (Raspberry Pi)
- Gunicorn WSGI server (2 workers)
- Cloudflare Tunnel for external access (no exposed ports)
- Automated backups every 6 hours
- Access via dieti-it.ch and adminer.dieti-it.ch

### Backup Strategy
Three backup options available:
- Simple 6-hour loop (`compose.backup.yml`)
- Cron-based every 6 hours (`compose.backup-cron.yml`)
- Daily at 2 AM (`compose.backup-daily.yml`)

## Common Tasks

### Adding New Course
1. Add course entry to `web/app/content/meta/courses.json`
2. Create course-specific metadata file if needed
3. Create lesson structure in `web/app/content/unterlagen/durchfuehrungen/<course-id>/`
4. Test course visibility and registration flow

### Debugging Deployment Issues
```bash
# Check service status
docker compose -f compose.yml -f compose.prod.yml ps

# View logs
docker compose -f compose.yml -f compose.prod.yml logs -n 50 webapp
docker compose -f compose.yml -f compose.prod.yml logs -n 50 cloudflared

# Test external connectivity
curl -I https://dieti-it.ch

# Check environment variables
test -f .env && echo "✅ .env ok" || echo "❌ .env fehlt"
```

### Running Single Test
```bash
cd web
python -m pytest tests/test_app.py::test_registration_form_post_valid -v
```