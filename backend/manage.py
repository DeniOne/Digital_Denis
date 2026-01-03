#!/usr/bin/env python
"""
Digital Den — Management CLI
═══════════════════════════════════════════════════════════════════════════

CLI tool for common management tasks.

Usage:
    python manage.py sync       # Auto-generate and apply migrations
    python manage.py migrate    # Apply pending migrations
    python manage.py status     # Check migration status
    python manage.py rollback   # Rollback last migration
"""

import argparse
import sys
import os

# Ensure backend is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def cmd_sync(args):
    """Sync database: generate and apply migrations."""
    from core.migrations import sync_database
    
    print("🔄 Syncing database...")
    success, message = sync_database()
    print(message)
    
    return 0 if success else 1


def cmd_migrate(args):
    """Apply pending migrations."""
    from core.migrations import run_upgrade, get_pending_migrations
    
    pending = get_pending_migrations()
    
    if not pending:
        print("✅ No pending migrations")
        return 0
    
    print(f"📦 Applying {len(pending)} migration(s)...")
    success = run_upgrade()
    
    if success:
        print("✅ Migrations applied successfully")
        return 0
    else:
        print("❌ Migration failed")
        return 1


def cmd_status(args):
    """Check migration status."""
    from core.migrations import check_migration_status, get_current_revision, get_head_revision, get_pending_migrations
    
    print("📊 Migration Status")
    print("─" * 40)
    
    current = get_current_revision()
    head = get_head_revision()
    pending = get_pending_migrations()
    
    print(f"Current revision: {current[:12] if current else '(none)'}")
    print(f"Head revision:    {head[:12] if head else '(none)'}")
    print(f"Pending:          {len(pending)} migration(s)")
    
    if pending:
        print("\n📋 Pending migrations:")
        for rev in pending:
            print(f"  → {rev[:12]}")
    
    is_up_to_date, status = check_migration_status()
    print(f"\n{status}")
    
    return 0


def cmd_rollback(args):
    """Rollback last migration."""
    from core.migrations import run_downgrade, get_current_revision
    
    current = get_current_revision()
    
    if not current:
        print("❌ No migrations to rollback")
        return 1
    
    print(f"⏪ Rolling back from {current[:12]}...")
    
    if args.yes or input("Are you sure? (y/N): ").lower() == 'y':
        success = run_downgrade("-1")
        if success:
            print("✅ Rollback successful")
            return 0
        else:
            print("❌ Rollback failed")
            return 1
    else:
        print("Cancelled")
        return 0


def cmd_generate(args):
    """Generate new migration."""
    from core.migrations import generate_migration
    
    message = args.message or "manual migration"
    print(f"📝 Generating migration: {message}")
    
    rev_id = generate_migration(message)
    
    if rev_id:
        print(f"✅ Created migration: {rev_id}")
        return 0
    else:
        print("ℹ️ No changes detected")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Digital Den Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # sync command
    sync_parser = subparsers.add_parser("sync", help="Auto-generate and apply migrations")
    sync_parser.set_defaults(func=cmd_sync)
    
    # migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Apply pending migrations")
    migrate_parser.set_defaults(func=cmd_migrate)
    
    # status command
    status_parser = subparsers.add_parser("status", help="Check migration status")
    status_parser.set_defaults(func=cmd_status)
    
    # rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback last migration")
    rollback_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    rollback_parser.set_defaults(func=cmd_rollback)
    
    # generate command
    generate_parser = subparsers.add_parser("generate", help="Generate new migration")
    generate_parser.add_argument("-m", "--message", help="Migration message")
    generate_parser.set_defaults(func=cmd_generate)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
