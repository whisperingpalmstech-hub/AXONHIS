from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from .models import (
    RpiwUserRole, RpiwRolePermission, RpiwRoleWorkflow,
    RpiwRoleSession, RpiwRoleComponent, RpiwRoleActivityLog
)


# Default role configurations - seeded on first access
DEFAULT_PERMISSIONS = {
    "doctor": [
        {"permission_key": "orders.create", "permission_label": "Create Clinical Orders", "resource_type": "orders", "can_create": True, "can_read": True, "can_update": True},
        {"permission_key": "diagnosis.update", "permission_label": "Update Diagnosis", "resource_type": "diagnosis", "can_create": True, "can_read": True, "can_update": True},
        {"permission_key": "notes.write", "permission_label": "Write Progress Notes", "resource_type": "notes", "can_create": True, "can_read": True, "can_update": True},
        {"permission_key": "prescriptions.create", "permission_label": "Prescribe Medications", "resource_type": "prescriptions", "can_create": True, "can_read": True},
        {"permission_key": "investigations.order", "permission_label": "Order Investigations", "resource_type": "investigations", "can_create": True, "can_read": True},
        {"permission_key": "patients.view", "permission_label": "View Patient Summary", "resource_type": "patients", "can_read": True},
    ],
    "nurse": [
        {"permission_key": "vitals.record", "permission_label": "Record Vitals", "resource_type": "vitals", "can_create": True, "can_read": True, "can_update": True},
        {"permission_key": "medications.administer", "permission_label": "Administer Medications", "resource_type": "medications", "can_create": True, "can_read": True, "can_update": True},
        {"permission_key": "notes.nursing", "permission_label": "Add Nursing Notes", "resource_type": "notes", "can_create": True, "can_read": True},
        {"permission_key": "tasks.execute", "permission_label": "Execute Tasks", "resource_type": "tasks", "can_create": True, "can_read": True, "can_update": True},
        {"permission_key": "patients.view", "permission_label": "View Patient Info", "resource_type": "patients", "can_read": True},
    ],
    "phlebotomist": [
        {"permission_key": "samples.collect", "permission_label": "Collect Samples", "resource_type": "samples", "can_create": True, "can_read": True, "can_update": True},
        {"permission_key": "barcodes.scan", "permission_label": "Scan Barcodes", "resource_type": "barcodes", "can_read": True},
        {"permission_key": "collection.status", "permission_label": "Update Collection Status", "resource_type": "collection", "can_read": True, "can_update": True},
        {"permission_key": "patients.view", "permission_label": "View Patient Info", "resource_type": "patients", "can_read": True},
    ],
}

DEFAULT_WORKFLOWS = {
    "doctor": [
        {"workflow_key": "review_summary", "workflow_label": "Review Patient Summary", "icon": "clipboard", "sort_order": 1, "route_path": "/workspace/summary"},
        {"workflow_key": "add_notes", "workflow_label": "Add Clinical Notes", "icon": "pencil", "sort_order": 2, "route_path": "/workspace/notes"},
        {"workflow_key": "order_investigations", "workflow_label": "Order Investigations", "icon": "flask", "sort_order": 3, "route_path": "/workspace/orders"},
        {"workflow_key": "prescribe_meds", "workflow_label": "Prescribe Medications", "icon": "pill", "sort_order": 4, "route_path": "/workspace/prescriptions"},
        {"workflow_key": "view_results", "workflow_label": "View Results", "icon": "chart", "sort_order": 5, "route_path": "/workspace/results"},
    ],
    "nurse": [
        {"workflow_key": "record_vitals", "workflow_label": "Record Vitals", "icon": "heart", "sort_order": 1, "route_path": "/workspace/vitals"},
        {"workflow_key": "administer_meds", "workflow_label": "Administer Medications", "icon": "pill", "sort_order": 2, "route_path": "/workspace/medications"},
        {"workflow_key": "monitor_patient", "workflow_label": "Monitor Patient Condition", "icon": "monitor", "sort_order": 3, "route_path": "/workspace/monitor"},
        {"workflow_key": "nursing_notes", "workflow_label": "Nursing Notes", "icon": "pencil", "sort_order": 4, "route_path": "/workspace/notes"},
        {"workflow_key": "execute_tasks", "workflow_label": "Execute Tasks", "icon": "check", "sort_order": 5, "route_path": "/workspace/tasks"},
    ],
    "phlebotomist": [
        {"workflow_key": "view_pending", "workflow_label": "View Pending Samples", "icon": "list", "sort_order": 1, "route_path": "/workspace/pending"},
        {"workflow_key": "collect_samples", "workflow_label": "Collect Blood Samples", "icon": "syringe", "sort_order": 2, "route_path": "/workspace/collect"},
        {"workflow_key": "scan_barcode", "workflow_label": "Barcode Scanner", "icon": "barcode", "sort_order": 3, "route_path": "/workspace/scanner"},
        {"workflow_key": "transport_status", "workflow_label": "Sample Transport Status", "icon": "truck", "sort_order": 4, "route_path": "/workspace/transport"},
    ],
}

DEFAULT_COMPONENTS = {
    "doctor": [
        {"component_key": "patient_summary_panel", "component_label": "Patient Summary", "component_type": "panel", "sort_order": 1},
        {"component_key": "clinical_action_panel", "component_label": "Clinical Actions", "component_type": "action_bar", "sort_order": 2},
        {"component_key": "ai_suggestions_panel", "component_label": "AI Suggestions", "component_type": "widget", "sort_order": 3},
        {"component_key": "order_history_panel", "component_label": "Order History", "component_type": "panel", "sort_order": 4},
        {"component_key": "diagnosis_panel", "component_label": "Diagnosis & Assessment", "component_type": "panel", "sort_order": 5},
    ],
    "nurse": [
        {"component_key": "vitals_recording_panel", "component_label": "Vitals Recording", "component_type": "panel", "sort_order": 1},
        {"component_key": "medication_admin_panel", "component_label": "Medication Administration", "component_type": "panel", "sort_order": 2},
        {"component_key": "task_list_panel", "component_label": "Task List", "component_type": "panel", "sort_order": 3},
        {"component_key": "patient_monitor_panel", "component_label": "Patient Monitor", "component_type": "widget", "sort_order": 4},
    ],
    "phlebotomist": [
        {"component_key": "sample_queue_panel", "component_label": "Sample Queue", "component_type": "panel", "sort_order": 1},
        {"component_key": "barcode_scanner_panel", "component_label": "Barcode Scanner", "component_type": "panel", "sort_order": 2},
        {"component_key": "collection_status_panel", "component_label": "Collection Status", "component_type": "widget", "sort_order": 3},
    ],
}


class RPIWService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def seed_role_defaults(self, role_code: str):
        """Seed default permissions, workflows, and components for a role if not already present."""
        # Check if already seeded
        existing = (await self.db.execute(
            select(RpiwRolePermission).where(RpiwRolePermission.role_code == role_code).limit(1)
        )).scalar_one_or_none()
        if existing:
            return  # Already seeded

        # Seed permissions
        for perm in DEFAULT_PERMISSIONS.get(role_code, []):
            self.db.add(RpiwRolePermission(role_code=role_code, **perm))

        # Seed workflows
        for wf in DEFAULT_WORKFLOWS.get(role_code, []):
            self.db.add(RpiwRoleWorkflow(role_code=role_code, **wf))

        # Seed components
        for comp in DEFAULT_COMPONENTS.get(role_code, []):
            self.db.add(RpiwRoleComponent(role_code=role_code, **comp))

        await self.db.flush()

    # ─── User Role Management ──────────────────────────────────

    async def assign_role(self, data: dict):
        role = RpiwUserRole(**data)
        self.db.add(role)
        await self.db.flush()
        await self.seed_role_defaults(data["role_code"])
        return role

    async def get_user_roles(self, user_id: str):
        return (await self.db.execute(
            select(RpiwUserRole).where(RpiwUserRole.user_id == user_id, RpiwUserRole.is_active == True)
        )).scalars().all()

    async def get_primary_role(self, user_id: str):
        return (await self.db.execute(
            select(RpiwUserRole).where(
                RpiwUserRole.user_id == user_id,
                RpiwUserRole.is_primary == True,
                RpiwUserRole.is_active == True
            )
        )).scalar_one_or_none()

    async def get_all_roles(self):
        return (await self.db.execute(
            select(RpiwUserRole).where(RpiwUserRole.is_active == True).order_by(RpiwUserRole.assigned_at.desc())
        )).scalars().all()

    # ─── Permission Management ──────────────────────────────────

    async def get_role_permissions(self, role_code: str):
        return (await self.db.execute(
            select(RpiwRolePermission).where(RpiwRolePermission.role_code == role_code, RpiwRolePermission.is_active == True)
        )).scalars().all()

    async def check_permission(self, role_code: str, permission_key: str) -> bool:
        perm = (await self.db.execute(
            select(RpiwRolePermission).where(
                RpiwRolePermission.role_code == role_code,
                RpiwRolePermission.permission_key == permission_key,
                RpiwRolePermission.is_active == True
            )
        )).scalar_one_or_none()
        return perm is not None

    # ─── Workflow Management ──────────────────────────────────

    async def get_role_workflows(self, role_code: str):
        return (await self.db.execute(
            select(RpiwRoleWorkflow).where(RpiwRoleWorkflow.role_code == role_code, RpiwRoleWorkflow.is_active == True)
            .order_by(RpiwRoleWorkflow.sort_order)
        )).scalars().all()

    # ─── Component Management ──────────────────────────────────

    async def get_role_components(self, role_code: str):
        return (await self.db.execute(
            select(RpiwRoleComponent).where(RpiwRoleComponent.role_code == role_code, RpiwRoleComponent.is_active == True)
            .order_by(RpiwRoleComponent.sort_order)
        )).scalars().all()

    # ─── Session Management ──────────────────────────────────

    async def create_session(self, user_id: str, role_code: str, department: str = None):
        # Deactivate old sessions
        await self.db.execute(
            update(RpiwRoleSession).where(RpiwRoleSession.user_id == user_id).values(is_active=False)
        )
        session = RpiwRoleSession(user_id=user_id, role_code=role_code, department=department)
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_active_session(self, user_id: str):
        return (await self.db.execute(
            select(RpiwRoleSession).where(RpiwRoleSession.user_id == user_id, RpiwRoleSession.is_active == True)
        )).scalar_one_or_none()

    async def update_session_workspace(self, session_id: str, workspace: str):
        session = (await self.db.execute(
            select(RpiwRoleSession).where(RpiwRoleSession.id == session_id)
        )).scalar_one_or_none()
        if session:
            session.active_workspace = workspace
            session.last_activity = datetime.now(timezone.utc)
            await self.db.flush()
        return session

    # ─── Workspace Configuration ──────────────────────────────────

    async def get_workspace_config(self, role_code: str):
        """Get full workspace configuration for a role (permissions + workflows + components)."""
        await self.seed_role_defaults(role_code)
        permissions = await self.get_role_permissions(role_code)
        workflows = await self.get_role_workflows(role_code)
        components = await self.get_role_components(role_code)
        return {"permissions": permissions, "workflows": workflows, "components": components}

    # ─── Activity Logging ──────────────────────────────────

    async def log_activity(self, data: dict):
        log = RpiwRoleActivityLog(**data)
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_activity_logs(self, user_id: str = None, role_code: str = None, limit: int = 50):
        q = select(RpiwRoleActivityLog).order_by(RpiwRoleActivityLog.performed_at.desc()).limit(limit)
        if user_id:
            q = q.where(RpiwRoleActivityLog.user_id == user_id)
        if role_code:
            q = q.where(RpiwRoleActivityLog.role_code == role_code)
        return (await self.db.execute(q)).scalars().all()
