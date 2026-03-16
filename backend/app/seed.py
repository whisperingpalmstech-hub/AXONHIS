"""
Seed data – creates default roles, permissions, and admin user.

Run: python -m app.seed
Or via:  docker compose exec backend python -m app.seed
"""
import asyncio
import uuid

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.core.auth.models import Permission, Role, RolePermission, User, UserRole
from app.core.auth.services import hash_password
from app.core.config.models import Configuration


# ── Default Permissions ───────────────────────────────────────────────────

DEFAULT_PERMISSIONS = [
    # Patient
    ("view_patient", "View Patient", "patients"),
    ("create_patient", "Create Patient", "patients"),
    ("edit_patient", "Edit Patient", "patients"),
    # Orders
    ("create_order", "Create Order", "orders"),
    ("approve_order", "Approve Order", "orders"),
    ("cancel_order", "Cancel Order", "orders"),
    ("view_orders", "View Orders", "orders"),
    # Billing
    ("view_billing", "View Billing", "billing"),
    ("modify_billing", "Modify Billing", "billing"),
    # Lab
    ("view_lab", "View Lab Results", "lab"),
    ("enter_lab_results", "Enter Lab Results", "lab"),
    # Pharmacy
    ("view_pharmacy", "View Pharmacy", "pharmacy"),
    ("dispense_medication", "Dispense Medication", "pharmacy"),
    # Administration
    ("manage_users", "Manage Users", "admin"),
    ("manage_roles", "Manage Roles", "admin"),
    ("view_audit_logs", "View Audit Logs", "admin"),
    ("manage_config", "Manage Configuration", "admin"),
    ("system_admin", "System Admin (Full Access)", "admin"),
    # Notifications
    ("manage_notifications", "Manage Notifications", "notifications"),
    # Files
    ("upload_files", "Upload Files", "files"),
    ("delete_files", "Delete Files", "files"),
]


# ── Default Roles ─────────────────────────────────────────────────────────

DEFAULT_ROLES = {
    "administrator": {
        "display_name": "Administrator",
        "description": "Full system access",
        "permissions": ["system_admin"],
    },
    "doctor": {
        "display_name": "Doctor",
        "description": "Clinician with order and patient access",
        "permissions": [
            "view_patient", "create_patient", "edit_patient",
            "create_order", "approve_order", "cancel_order", "view_orders",
            "view_billing", "view_lab", "upload_files",
        ],
    },
    "nurse": {
        "display_name": "Nurse",
        "description": "Nursing staff with task and vital sign access",
        "permissions": [
            "view_patient", "edit_patient", "view_orders",
            "view_lab", "upload_files",
        ],
    },
    "lab_technician": {
        "display_name": "Lab Technician",
        "description": "Laboratory staff",
        "permissions": [
            "view_patient", "view_orders", "view_lab", "enter_lab_results",
        ],
    },
    "pharmacist": {
        "display_name": "Pharmacist",
        "description": "Pharmacy staff",
        "permissions": [
            "view_patient", "view_orders", "view_pharmacy", "dispense_medication",
        ],
    },
    "billing_officer": {
        "display_name": "Billing Officer",
        "description": "Billing and finance staff",
        "permissions": [
            "view_patient", "view_billing", "modify_billing", "view_orders",
        ],
    },
}


# ── Default Configuration ─────────────────────────────────────────────────

DEFAULT_CONFIG = [
    ("hospital_name", "AXONHIS Hospital", "Name of the hospital", "general"),
    ("timezone", "Asia/Kolkata", "System timezone", "general"),
    ("default_language", "en", "Default system language", "general"),
    ("password_policy", "min_8_chars_mixed", "Password policy level", "security"),
    ("session_timeout_minutes", "60", "Session timeout in minutes", "security"),
    ("max_failed_login_attempts", "5", "Max failed login attempts before lockout", "security"),
    ("lockout_duration_minutes", "30", "Account lockout duration in minutes", "security"),
]


async def seed_database() -> None:
    """Seed the database with default roles, permissions, admin user, and config."""
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(select(Permission).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        # Create permissions
        perm_map: dict[str, Permission] = {}
        for code, display_name, category in DEFAULT_PERMISSIONS:
            p = Permission(code=code, display_name=display_name, category=category)
            db.add(p)
            perm_map[code] = p
        await db.flush()
        print(f"  Created {len(perm_map)} permissions")

        # Create roles with permission assignments
        role_map: dict[str, Role] = {}
        for role_name, role_data in DEFAULT_ROLES.items():
            role = Role(
                name=role_name,
                display_name=role_data["display_name"],
                description=role_data["description"],
                is_system=True,
            )
            db.add(role)
            await db.flush()
            for perm_code in role_data["permissions"]:
                db.add(RolePermission(role_id=role.id, permission_id=perm_map[perm_code].id))
            role_map[role_name] = role
        await db.flush()
        print(f"  Created {len(role_map)} roles")

        # Create default admin user
        admin = User(
            email="admin@axonhis.com",
            password_hash=hash_password("Admin@123"),
            first_name="System",
            last_name="Administrator",
        )
        db.add(admin)
        await db.flush()
        db.add(UserRole(user_id=admin.id, role_id=role_map["administrator"].id))
        await db.flush()
        print(f"  Created admin user: admin@axonhis.com / Admin@123")

        # Create default configuration
        for key, value, description, category in DEFAULT_CONFIG:
            db.add(Configuration(key=key, value=value, description=description, category=category))
        await db.flush()
        print(f"  Created {len(DEFAULT_CONFIG)} configuration entries")

        await db.commit()
        print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_database())
