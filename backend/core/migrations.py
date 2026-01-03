"""
Digital Den — Migration Helper
═══════════════════════════════════════════════════════════════════════════

Utilities for database migration management.
"""

import os
import sys
from typing import Optional, Tuple, List

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_alembic_config():
    """Get Alembic configuration."""
    from alembic.config import Config
    from pathlib import Path
    
    backend_dir = Path(__file__).parent.parent
    alembic_ini = backend_dir / "alembic.ini"
    
    if not alembic_ini.exists():
        raise FileNotFoundError(f"alembic.ini not found at {alembic_ini}")
    
    config = Config(str(alembic_ini))
    
    # Override database URL from environment
    database_url = os.getenv("DATABASE_URL", "postgresql://denis:denis_dev_2024@localhost:5434/digital_denis")
    config.set_main_option("sqlalchemy.url", database_url)
    
    return config


def get_current_revision() -> Optional[str]:
    """Get current database revision."""
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import create_engine
    
    database_url = os.getenv("DATABASE_URL", "postgresql://denis:denis_dev_2024@localhost:5434/digital_denis")
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            return context.get_current_revision()
    except Exception as e:
        print(f"Error getting current revision: {e}")
        return None


def get_head_revision() -> Optional[str]:
    """Get latest revision from migration scripts."""
    from alembic.script import ScriptDirectory
    
    config = get_alembic_config()
    script = ScriptDirectory.from_config(config)
    
    head = script.get_current_head()
    return head


def get_pending_migrations() -> List[str]:
    """Get list of pending migrations."""
    from alembic.script import ScriptDirectory
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import create_engine
    
    config = get_alembic_config()
    script = ScriptDirectory.from_config(config)
    
    database_url = os.getenv("DATABASE_URL", "postgresql://denis:denis_dev_2024@localhost:5434/digital_denis")
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current = context.get_current_revision()
            
            # Get all revisions between current and head
            if current is None:
                # No migrations applied yet
                revisions = list(script.iterate_revisions("base", "head"))
            else:
                revisions = list(script.iterate_revisions(current, "head"))
            
            # Filter to only pending (not current)
            pending = [rev.revision for rev in revisions if rev.revision != current]
            return pending
            
    except Exception as e:
        print(f"Error getting pending migrations: {e}")
        return []


def check_migration_status() -> Tuple[bool, str]:
    """
    Check if database is up to date with migrations.
    
    Returns:
        Tuple of (is_up_to_date, status_message)
    """
    current = get_current_revision()
    head = get_head_revision()
    pending = get_pending_migrations()
    
    if current is None and head is None:
        return True, "No migrations defined yet"
    
    if current == head:
        return True, f"Database is up to date (revision: {current[:8] if current else 'none'})"
    
    if pending:
        return False, f"⚠️ {len(pending)} pending migration(s): {', '.join(p[:8] for p in pending)}"
    
    return True, f"Current: {current[:8] if current else 'none'}, Head: {head[:8] if head else 'none'}"


def run_upgrade(revision: str = "head") -> bool:
    """
    Apply migrations up to specified revision.
    
    Args:
        revision: Target revision, default "head"
        
    Returns:
        True if successful
    """
    from alembic import command
    
    try:
        config = get_alembic_config()
        command.upgrade(config, revision)
        return True
    except Exception as e:
        print(f"Migration error: {e}")
        return False


def run_downgrade(revision: str = "-1") -> bool:
    """
    Rollback migrations.
    
    Args:
        revision: Target revision, default "-1" (one step back)
        
    Returns:
        True if successful
    """
    from alembic import command
    
    try:
        config = get_alembic_config()
        command.downgrade(config, revision)
        return True
    except Exception as e:
        print(f"Rollback error: {e}")
        return False


def generate_migration(message: str = "auto migration") -> Optional[str]:
    """
    Generate new migration from model changes.
    
    Args:
        message: Migration description
        
    Returns:
        Revision ID if created, None if no changes detected
    """
    from alembic import command
    from io import StringIO
    import sys
    
    try:
        config = get_alembic_config()
        
        # Capture output to check if migration was created
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        command.revision(config, autogenerate=True, message=message)
        
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        if "Generating" in output:
            # Extract revision ID from output
            for line in output.split("\n"):
                if "Generating" in line:
                    print(line)
                    # Extract revision from path
                    parts = line.split("/")[-1] if "/" in line else line.split("\\")[-1]
                    rev_id = parts.split("_")[0] if parts else None
                    return rev_id
        else:
            print("No changes detected in models")
            return None
            
    except Exception as e:
        print(f"Error generating migration: {e}")
        return None


def sync_database() -> Tuple[bool, str]:
    """
    Full sync: generate migration (if needed) and apply.
    
    Returns:
        Tuple of (success, message)
    """
    print("🔍 Checking for model changes...")
    
    # Generate migration if there are changes
    rev_id = generate_migration("auto sync")
    
    if rev_id:
        print(f"📝 Generated migration: {rev_id}")
    else:
        print("✅ No model changes detected")
    
    # Apply any pending migrations
    pending = get_pending_migrations()
    
    if pending:
        print(f"📦 Applying {len(pending)} migration(s)...")
        success = run_upgrade()
        if success:
            return True, f"✅ Applied {len(pending)} migration(s)"
        else:
            return False, "❌ Migration failed"
    
    return True, "✅ Database is up to date"
