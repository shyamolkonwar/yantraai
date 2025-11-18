#!/usr/bin/env python3
"""
Command Line Interface for Yantra AI Backend
"""

import os
import sys
import click
from alembic.config import Config
from alembic import command

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.core.database import engine, Base
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.core.database import SessionLocal


@click.group()
def cli():
    """Yantra AI Backend CLI"""
    pass


@cli.command()
def init_db():
    """Initialize the database with all tables"""
    click.echo("Initializing database...")
    try:
        Base.metadata.create_all(bind=engine)
        click.echo("Database initialized successfully!")
    except Exception as e:
        click.echo(f"Error initializing database: {e}", err=True)


@cli.command()
def migrate():
    """Run database migrations"""
    click.echo("Running database migrations...")
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        click.echo("Migrations completed successfully!")
    except Exception as e:
        click.echo(f"Error running migrations: {e}", err=True)


@cli.command()
@click.option('--email', prompt='Email', help='User email')
@click.option('--password', prompt='Password', hide_input=True, confirmation_prompt=True, help='User password')
@click.option('--role', type=click.Choice(['uploader', 'reviewer', 'admin']), default='uploader', help='User role')
def create_user(email, password, role):
    """Create a new user"""
    click.echo(f"Creating user: {email}")
    try:
        db = SessionLocal()

        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            click.echo(f"User {email} already exists!", err=True)
            return

        # Create new user
        user = User(
            email=email,
            password_hash=get_password_hash(password),
            role=UserRole[role.upper()],
            is_active=True
        )

        db.add(user)
        db.commit()

        click.echo(f"User {email} created successfully with role: {role}")

    except Exception as e:
        click.echo(f"Error creating user: {e}", err=True)
    finally:
        db.close()


@cli.command()
def list_users():
    """List all users"""
    click.echo("Listing users:")
    try:
        db = SessionLocal()
        users = db.query(User).all()

        if not users:
            click.echo("No users found.")
            return

        for user in users:
            status = "Active" if user.is_active else "Inactive"
            click.echo(f"  {user.email} - {user.role.value} - {status}")

    except Exception as e:
        click.echo(f"Error listing users: {e}", err=True)
    finally:
        db.close()


@cli.command()
@click.option('--message', default='Initial migration', help='Migration message')
def create_migration(message):
    """Create a new migration"""
    click.echo(f"Creating migration: {message}")
    try:
        alembic_cfg = Config("alembic.ini")
        command.revision(alembic_cfg, autogenerate=True, message=message)
        click.echo("Migration created successfully!")
    except Exception as e:
        click.echo(f"Error creating migration: {e}", err=True)


@cli.command()
def reset_db():
    """Reset the database (WARNING: This will delete all data!)"""
    if click.confirm('Are you sure you want to reset the database? This will delete all data!'):
        click.echo("Resetting database...")
        try:
            alembic_cfg = Config("alembic.ini")
            command.downgrade(alembic_cfg, "base")
            command.upgrade(alembic_cfg, "head")
            click.echo("Database reset successfully!")
        except Exception as e:
            click.echo(f"Error resetting database: {e}", err=True)


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
def serve(host, port, reload):
    """Start the FastAPI server"""
    click.echo(f"Starting server on {host}:{port}")
    try:
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload
        )
    except Exception as e:
        click.echo(f"Error starting server: {e}", err=True)


@cli.command()
def worker():
    """Start the RQ worker"""
    click.echo("Starting RQ worker...")
    try:
        from rq import Worker, Connection
        from app.services.job_queue import redis_conn

        with Connection(redis_conn):
            worker = Worker(['yantra-ai-queue'])
            worker.work()
    except Exception as e:
        click.echo(f"Error starting worker: {e}", err=True)


if __name__ == '__main__':
    cli()