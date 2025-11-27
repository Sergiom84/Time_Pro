# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Time Pro is a multi-tenant time tracking and employee management system built with Flask. It supports two plans (Lite and Pro) and provides comprehensive employee time management, leave requests, work pauses, and reporting capabilities.

**Tech Stack:**
- Backend: Flask with Blueprint-based architecture
- ORM: SQLAlchemy with custom TenantAwareQuery for multi-tenant filtering
- Database: PostgreSQL (Supabase in production) / SQLite (development)
- Frontend: Jinja2 templates + Tailwind CSS + JavaScript
- Real-time: Flask-SocketIO with eventlet
- Build: Vite for asset compilation
- Migrations: Alembic

## Development Commands

### Starting the Application

**Development (Lite plan):**
```bash
bash run_lite.sh
```

**Development (Pro plan):**
```bash
bash run_pro.sh
```

**Manual start with specific plan:**
```bash
export APP_PLAN=lite  # or 'pro'
python3 main.py
```

**Stop all instances:**
```bash
bash stop_app.sh
```

**Check status:**
```bash
bash check_status.sh
```

### Database Migrations

**Create a new migration:**
```bash
flask db migrate -m "Description of changes"
```

**Apply migrations:**
```bash
flask db upgrade
```

**Rollback migration:**
```bash
flask db downgrade
```

### Testing

**Run multi-tenant isolation tests:**
```bash
python3 test_multitenant_isolation.py
```

**Test plan configuration:**
```bash
python3 test_plan_system.py
```

### Deployment

Application is configured for deployment on Render/Heroku using the `Procfile`:
```bash
gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:$PORT wsgi:app --timeout 120
```

## Architecture Overview

### Multi-Tenant System

**Critical:** Time Pro uses a sophisticated multi-tenant architecture that isolates data by `client_id`. This is enforced automatically at the ORM level.

**Key Components:**
1. **TenantAwareQuery** (`models/database.py`) - Custom SQLAlchemy Query class that automatically filters all queries by `client_id` from session
2. **Multi-tenant utilities** (`utils/multitenant.py`) - Helper functions for client context management
3. **Session-based isolation** - `client_id` is stored in Flask session on login and used for all subsequent queries

**Tenant Models** (automatically filtered):
- User
- TimeRecord
- EmployeeStatus
- WorkPause
- LeaveRequest
- SystemConfig

**Important:** Category should be in TENANT_MODELS but currently is not - if working with categories, add it to the list in `models/database.py:10-17`.

### Blueprint Structure

The application uses Flask Blueprints for modular organization:

- **auth_bp** (`routes/auth.py`) - Authentication (login, logout, registration)
- **time_bp** (`routes/time.py`) - Time tracking (check-in/out, pauses, employee dashboard)
- **admin_bp** (`routes/admin.py`) - Admin functions (user management, dashboard, calendar, leave requests)
- **export_bp** (`routes/export.py`) - Data export (Excel, PDF)

### Plan System

Two plans are available: **Lite** and **Pro**, configured via `APP_PLAN` environment variable.

**Key differences:**
- Lite: Max 5 employees, single center, no multi-center features
- Pro: Unlimited employees, multiple centers, full feature set

**Configuration files:**
- `plan_config.py` - Global plan configuration
- `utils/multitenant.py:get_client_config()` - Client-specific plan config

### Database Models

**Core models** in `models/models.py`:

1. **Client** - Multi-tenant parent (id, name, slug, plan, branding)
2. **Category** - Dynamic employee categories per client (currently exists but not fully integrated - uses ENUM in User model instead)
3. **User** - Employees and admins (client_id, username, email, role, categoria ENUM)
4. **TimeRecord** - Check-in/out records
5. **EmployeeStatus** - Daily employee status (Trabajado, Baja, Ausente, Vacaciones)
6. **WorkPause** - Work pauses (Descanso, Almuerzo, Médicos, Desplazamientos)
7. **LeaveRequest** - Leave/absence requests
8. **SystemConfig** - Key-value configuration per client

**Important Note on Categories:**
- Current implementation: User has an ENUM field `categoria` with hardcoded values ("Coordinador", "Empleado", "Gestor")
- Future enhancement: Should use FK to Category model for dynamic per-client categories
- Documentation in IMPLEMENTATION_GUIDE.md covers the migration path

## Code Patterns and Best Practices

### Multi-Tenant Query Pattern

**Always ensure client_id is set:**
```python
from flask import session

# Reading with automatic filtering (TenantAwareQuery handles this)
users = User.query.all()  # Automatically filtered by session['client_id']

# Creating new records - MUST include client_id
client_id = session.get('client_id', 1)
new_record = TimeRecord(
    client_id=client_id,
    user_id=user_id,
    # ... other fields
)
```

**Bypass tenant filter (use sparingly):**
```python
# Only for admin operations across all clients
all_clients = Client.query.bypass_tenant_filter().all()
```

### Session Management

Client context is established at login:
```python
# In routes/auth.py
session['user_id'] = user.id
session['client_id'] = user.client_id
session['is_admin'] = user.role in ['admin', 'super_admin']
```

### Plan Feature Checks

**In routes:**
```python
import plan_config

if plan_config.is_lite():
    # Lite-specific logic
    max_employees = plan_config.MAX_EMPLOYEES  # 5
    
if plan_config.has_feature('multi_center'):
    # Pro-only feature
```

**In templates:**
```jinja2
{% if config.features.multi_center %}
    <!-- Show center selector -->
{% endif %}
```

### Database Connection (Important for Windows/WSL)

The application includes an IPv4 fix for Supabase connections in `main.py:10-24`. This MUST be loaded before any SQLAlchemy imports to avoid IPv6 timeout issues on Windows/WSL.

**Connection pooling:**
- Development: pool_size=1, max_overflow=2 (Supabase free tier)
- Production: pool_size=10, max_overflow=20
- Always uses Transaction Pooler (port 6543) for Supabase

## Common Development Tasks

### Adding a New Route

1. Choose appropriate blueprint (`auth_bp`, `time_bp`, `admin_bp`, `export_bp`)
2. Add route decorator and function
3. Ensure multi-tenant filtering is applied for data access
4. Create corresponding template in `src/templates/`

Example:
```python
# In routes/admin.py
@admin_bp.route('/new-feature', methods=['GET', 'POST'])
@login_required
def new_feature():
    client_id = session.get('client_id')
    # Query automatically filtered by TenantAwareQuery
    users = User.query.filter_by(is_active=True).all()
    return render_template('new_feature.html', users=users)
```

### Working with Categories

**Current state:**
- User.categoria is a PostgreSQL ENUM (hardcoded values)
- DEFAULT_CATEGORIES defined in `routes/admin.py:20`
- Category model exists but is not connected to User

**If modifying category system:**
1. Review `IMPLEMENTATION_GUIDE.md` for complete migration steps
2. Update `models/models.py` to change User.categoria from ENUM to FK
3. Add Category to TENANT_MODELS in `models/database.py`
4. Create Alembic migration
5. Update all templates and routes that reference User.categoria

### Adding a Database Model

1. Define model in `models/models.py`
2. Include `client_id` column with FK to Client for multi-tenant models
3. Add model name to TENANT_MODELS in `models/database.py` if it needs tenant filtering
4. Create migration: `flask db migrate -m "Add ModelName"`
5. Apply migration: `flask db upgrade`

### Email Notifications

Configured via Flask-Mail with environment variables:
- MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD
- Email sending handled by APScheduler for scheduled notifications
- See `tasks/scheduler.py` for automated email jobs

### Real-time Updates

Flask-SocketIO is configured with eventlet for real-time features:
```python
from flask_socketio import emit

socketio.emit('event_name', {'data': 'value'}, room=room_name)
```

## Project File Structure

```
Time_Pro/
├── main.py                  # Flask app entry point (MUST be first to load)
├── plan_config.py           # Plan configuration (Lite/Pro)
├── models/
│   ├── database.py         # TenantAwareQuery definition
│   ├── models.py           # All SQLAlchemy models
│   └── email_log.py        # Email logging model
├── routes/                  # Flask Blueprints
│   ├── auth.py             # Authentication routes
│   ├── time.py             # Time tracking routes
│   ├── admin.py            # Admin/management routes
│   └── export.py           # Export functionality
├── src/
│   ├── templates/          # Jinja2 HTML templates
│   ├── static/             # Compiled CSS/JS assets
│   └── pages/              # React components (minimal usage)
├── utils/
│   ├── multitenant.py      # Multi-tenant utilities
│   └── file_utils.py       # File handling utilities
├── migrations/              # Alembic migrations
│   └── versions/           # Migration scripts
├── tasks/
│   └── scheduler.py        # APScheduler background jobs
├── config/
│   └── supabase_config.py  # Supabase credentials
├── static/                  # Public assets
├── requirements.txt         # Python dependencies
├── Procfile                # Deployment configuration
└── *.sh                    # Shell scripts for running app

Documentation Files:
├── INDICE_DOCUMENTACION.md        # Documentation index
├── PROJECT_STRUCTURE_ANALYSIS.md  # Deep architecture analysis
├── IMPLEMENTATION_GUIDE.md        # Step-by-step implementation guides
├── MULTITENANT_RESUMEN.md         # Multi-tenant implementation summary
├── GUIA_RAPIDA.md                 # Quick start guide (Spanish)
└── WARP.md                        # This file
```

## Important Notes

### Security

- **Never commit** `.env` file (use `.env.example` as template)
- Database passwords in DATABASE_URL should be URL-encoded if they contain special characters (e.g., @ becomes %40)
- Session secret key should be randomly generated in production
- Multi-tenant filtering provides data isolation, but always verify client_id context in sensitive operations

### Known Issues and Considerations

1. **Category System:** Current ENUM-based category system is not dynamic per client. See IMPLEMENTATION_GUIDE.md for migration to FK-based system.

2. **IPv6 Connection Issues:** The IPv4 fix in main.py MUST stay at the top before any imports. Don't move or remove it.

3. **Connection Pooling:** Development uses minimal pooling (pool_size=1) to stay within Supabase free tier limits. Increase for production.

4. **Template Context:** User context and greetings are automatically injected via context processor in main.py (lines 174-200+).

### Environment Variables

Required in `.env`:
- `DATABASE_URL` - PostgreSQL connection string (use Transaction Pooler port 6543)
- `SECRET_KEY` - Flask session secret
- `APP_PLAN` - 'lite' or 'pro'
- `MAIL_*` - Email configuration for notifications
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` - Supabase API config

## Additional Documentation

For detailed information, consult:
- **INDICE_DOCUMENTACION.md** - Complete documentation index with reading order
- **PROJECT_STRUCTURE_ANALYSIS.md** - In-depth architecture analysis
- **IMPLEMENTATION_GUIDE.md** - Step-by-step guides with code examples
- **MULTITENANT_RESUMEN.md** - Multi-tenant implementation details
- **GUIA_RAPIDA.md** - Quick start guide (Spanish)
