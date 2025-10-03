# Saleor Development Environment Setup Guide for Windows

This comprehensive guide will walk you through setting up the Saleor development environment on Windows. Follow these steps in order to get Saleor running on your local machine.

## Prerequisites

Before starting, ensure you have:
- Windows 10 or later
- Administrator privileges
- Git for Windows installed
- PowerShell or Command Prompt

## A-Z Setup Guide

### A. Install Required Tools

1. **Install Python 3.12**:
   - Download Python 3.12 from [python.org](https://www.python.org/downloads/)
   - During installation, make sure to check "Add Python to PATH"

2. **Install Git**:
   - Download Git for Windows from [git-scm.com](https://git-scm.com/download/win)
   - Install with default settings

3. **Install Docker Desktop**:
   - Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
   - Install and follow the setup wizard
   - Restart your computer if prompted

### B. Install uv Package Manager

Open PowerShell as Administrator and run:
```powershell
# Install uv via pip
pip install uv
```

**Reason**: Saleor uses `uv` as its package manager for faster dependency resolution and installation.

### C. Clone the Repository

```powershell
# Clone the Saleor repository
git clone https://github.com/saleor/saleor.git
cd saleor
```

**Reason**: You need the source code to run and develop Saleor locally.

### D. Set Up Python Environment

```powershell
# Install Python 3.12 (if not already installed)
uv python install 3.12

# Sync project dependencies
uv sync
```

**Reason**: Saleor requires Python 3.12, and `uv sync` installs all project dependencies as specified in [pyproject.toml](cci:7://file:///home/piyush/singleshot/saleor/pyproject.toml:0:0-0:0).

### E. Install Development Tools

```powershell
# Install pre-commit hooks
uv run pre-commit install
```

**Reason**: Pre-commit hooks help maintain code quality by running checks before commits.

### F. Configure Environment Variables

```powershell
# Create .env file from example
copy .env.example .env
```

**Reason**: The `.env` file contains environment-specific configuration for the application.

### G. Start Required Services

```powershell
# Navigate to devcontainer directory
cd .devcontainer

# Start required services (database, dashboard, Redis, Mailpit)
docker-compose up -d db dashboard redis mailpit

# Return to project root
cd ..
```

**Reason**: Saleor requires several services to run properly:
- PostgreSQL database for data storage
- Redis for caching and task queue
- Mailpit for email testing
- Dashboard for the admin interface

### H. Run Database Migrations

```powershell
# Apply database migrations
uv run python manage.py migrate
```

**Reason**: Database migrations create the necessary tables and schema structure in the database.

### I. Populate Database with Sample Data

```powershell
# Populate database with sample data and create superuser
uv run python manage.py populatedb --createsuperuser
```

**Reason**: This command creates sample products, users, orders, and other data for testing, plus a superuser account for admin access.

### J. Build GraphQL Schema

```powershell
# Generate GraphQL schema
uv run poe build-schema
```

**Reason**: This creates the GraphQL schema file that defines the API structure.

### K. Start Development Server

```powershell
# Start the development server
uv run poe start
```

**Reason**: This starts the main Saleor application with hot-reload capabilities.

### L. Start Celery Worker

```powershell
# Start Celery worker for background tasks
uv run poe worker
```

**Reason**: Celery handles background tasks like sending emails, processing payments, etc.

## Accessing the Application

Once everything is running, you can access:

- **Main Application**: http://127.0.0.1:8000
- **GraphQL Playground**: http://127.0.0.1:8000/graphql/
- **Admin Dashboard**: http://127.0.0.1:8000/admin/

Superuser credentials:
- **Email**: admin@example.com
- **Password**: admin

## Troubleshooting

### Docker Issues

If you encounter Docker issues:
1. Make sure Docker Desktop is running
2. Check that WSL 2 is installed and enabled
3. Ensure Docker Desktop is set to use WSL 2 backend

### PATH Issues

If `uv` commands are not found:
1. Add Python Scripts directory to PATH:
   - Usually located at `C:\Users\[Username]\AppData\Local\Programs\Python\Python312\Scripts\`
2. Or add uv installation path to PATH:
   - Usually located at `C:\Users\[Username]\AppData\Roaming\Python\Python312\Scripts\`

### Windows-Specific Issues

1. **Line endings**: Git might convert line endings. Set Git to not convert them:
   ```powershell
   git config --global core.autocrlf false
   ```

2. **File permissions**: Some scripts might not run due to execution policy. In PowerShell as Administrator:
   ```powershell
   Set-ExecutionPolicy RemoteSigned
   ```

## Useful Commands

```powershell
# Run tests
uv run poe test

# Run specific tests
uv run poe test saleor/graphql/app/tests

# Create new migrations
uv run python manage.py makemigrations

# Shell access
uv run poe shell

# Start Celery Beat scheduler
uv run poe scheduler
```

## Stopping Services

To stop all services:
```powershell
# Stop Docker services
cd .devcontainer && docker-compose down

# Stop the development server and Celery worker
# Press Ctrl+C in their respective terminal windows
```

## Alternative: Using Windows Subsystem for Linux (WSL)

For a more Linux-like experience, you can use WSL:

1. **Install WSL**:
   ```powershell
   wsl --install
   ```

2. **Install Ubuntu** from Microsoft Store

3. **Follow the Linux guide** within your WSL environment

This approach often provides better compatibility with development tools and fewer platform-specific issues.

This guide should get any beginner up and running with a fully functional Saleor development environment on Windows. The setup uses Docker Desktop for services and `uv` for Python dependency management, following Saleor's recommended development practices.
