from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
import json
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc

from app.core.clinical_rules.models import (
    MdClinicalRule,
    MdRuleExecution,
    MdRuleAlert,
    MdRuleVariable,
    RuleStatus,
    RuleSeverity,
    RuleTriggerType
)
from app.core.clinical_rules.schemas import (
    ClinicalRuleCreate,
    ClinicalRuleUpdate,
    RuleExecutionCreate,
    RuleEvaluationContext,
    RuleEvaluationResult,
    RuleSearchQuery
)


class ClinicalRuleEngine:
    """Clinical Rule Engine for evaluating and executing clinical decision support rules."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_rule(
        self,
        rule_data: ClinicalRuleCreate
    ) -> MdClinicalRule:
        """Create a new clinical rule."""
        rule = MdClinicalRule(
            rule_code=rule_data.rule_code,
            rule_name=rule_data.rule_name,
            rule_description=rule_data.rule_description,
            rule_category=rule_data.rule_category,
            rule_version=rule_data.rule_version,
            status=rule_data.status,
            severity=rule_data.severity,
            trigger_type=rule_data.trigger_type,
            condition_expression=rule_data.condition_expression,
            action_config=rule_data.action_config,
            priority=rule_data.priority,
            specialty_profile_id=rule_data.specialty_profile_id,
            facility_id=rule_data.facility_id,
            requires_approval=rule_data.requires_approval,
            auto_execute=rule_data.auto_execute,
            created_by=rule_data.created_by,
            effective_from=rule_data.effective_from,
            effective_to=rule_data.effective_to
        )
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def update_rule(
        self,
        rule_id: uuid.UUID,
        update_data: ClinicalRuleUpdate
    ) -> Optional[MdClinicalRule]:
        """Update an existing clinical rule."""
        query = select(MdClinicalRule).where(MdClinicalRule.rule_id == rule_id)
        result = await self.db.execute(query)
        rule = result.scalar_one_or_none()
        
        if not rule:
            return None
        
        if update_data.rule_name is not None:
            rule.rule_name = update_data.rule_name
        if update_data.rule_description is not None:
            rule.rule_description = update_data.rule_description
        if update_data.rule_category is not None:
            rule.rule_category = update_data.rule_category
        if update_data.status is not None:
            rule.status = update_data.status
        if update_data.severity is not None:
            rule.severity = update_data.severity
        if update_data.condition_expression is not None:
            rule.condition_expression = update_data.condition_expression
        if update_data.action_config is not None:
            rule.action_config = update_data.action_config
        if update_data.priority is not None:
            rule.priority = update_data.priority
        if update_data.requires_approval is not None:
            rule.requires_approval = update_data.requires_approval
        if update_data.auto_execute is not None:
            rule.auto_execute = update_data.auto_execute
        if update_data.updated_by is not None:
            rule.updated_by = update_data.updated_by
        if update_data.effective_from is not None:
            rule.effective_from = update_data.effective_from
        if update_data.effective_to is not None:
            rule.effective_to = update_data.effective_to
        
        rule.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def get_rule(
        self,
        rule_id: uuid.UUID
    ) -> Optional[MdClinicalRule]:
        """Get a specific clinical rule."""
        query = select(MdClinicalRule).where(MdClinicalRule.rule_id == rule_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def search_rules(
        self,
        query: RuleSearchQuery
    ) -> tuple[List[MdClinicalRule], int]:
        """Search clinical rules with filters."""
        conditions = []
        
        if query.rule_category:
            conditions.append(MdClinicalRule.rule_category == query.rule_category)
        
        if query.status:
            conditions.append(MdClinicalRule.status == query.status)
        
        if query.severity:
            conditions.append(MdClinicalRule.severity == query.severity)
        
        if query.trigger_type:
            conditions.append(MdClinicalRule.trigger_type == query.trigger_type)
        
        if query.specialty_profile_id:
            conditions.append(MdClinicalRule.specialty_profile_id == query.specialty_profile_id)
        
        if query.facility_id:
            conditions.append(MdClinicalRule.facility_id == query.facility_id)
        
        # Get total count
        count_query = select(func.count(MdClinicalRule.rule_id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()
        
        # Get paginated results
        rules_query = select(MdClinicalRule)
        if conditions:
            rules_query = rules_query.where(and_(*conditions))
        
        rules_query = rules_query.order_by(desc(MdClinicalRule.priority), desc(MdClinicalRule.created_at)).offset(
            query.offset
        ).limit(query.limit)
        
        rules_result = await self.db.execute(rules_query)
        rules = rules_result.scalars().all()
        
        return list(rules), total_count

    async def evaluate_rule(
        self,
        rule: MdClinicalRule,
        context: RuleEvaluationContext
    ) -> bool:
        """Evaluate if a rule matches the given context."""
        try:
            condition = rule.condition_expression
            
            # Simple condition evaluation - can be extended with a proper expression engine
            # For now, we'll do basic JSON path matching
            if "conditions" in condition:
                for cond in condition["conditions"]:
                    field = cond.get("field")
                    operator = cond.get("operator")
                    value = cond.get("value")
                    
                    if not self._evaluate_condition(field, operator, value, context):
                        return False
            
            return True
        except Exception as e:
            print(f"Error evaluating rule {rule.rule_id}: {e}")
            return False

    def _evaluate_condition(
        self,
        field: str,
        operator: str,
        value: Any,
        context: RuleEvaluationContext
    ) -> bool:
        """Evaluate a single condition."""
        # Extract value from context using field path
        context_value = self._get_nested_value(field, context.dict())
        
        if operator == "equals":
            return context_value == value
        elif operator == "not_equals":
            return context_value != value
        elif operator == "greater_than":
            return context_value > value
        elif operator == "less_than":
            return context_value < value
        elif operator == "contains":
            return value in str(context_value)
        elif operator == "in":
            return context_value in value
        elif operator == "exists":
            return context_value is not None
        else:
            return False

    def _get_nested_value(
        self,
        field_path: str,
        data: Dict[str, Any]
    ) -> Any:
        """Get nested value from dictionary using dot notation."""
        keys = field_path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    async def execute_rule(
        self,
        rule_id: uuid.UUID,
        context: RuleEvaluationContext
    ) -> Dict[str, Any]:
        """Execute a rule and create execution record."""
        rule = await self.get_rule(rule_id)
        if not rule:
            return {"error": "Rule not found"}
        
        start_time = time.time()
        
        # Create execution record
        execution = MdRuleExecution(
            rule_id=rule_id,
            patient_id=context.patient_id,
            encounter_id=context.encounter_id,
            trigger_event=context.trigger_event,
            trigger_data=context.trigger_data,
            execution_status="TRIGGERED",
            rule_matched=False,
            action_taken={}
        )
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)
        
        try:
            # Evaluate rule
            rule_matched = await self.evaluate_rule(rule, context)
            execution.rule_matched = rule_matched
            
            if rule_matched:
                # Execute actions
                actions = await self._execute_actions(rule, context, execution)
                execution.action_taken = actions
                
                # Create alerts if configured
                if rule.action_config.get("create_alert"):
                    await self._create_alert(rule, execution, context)
                
                execution.execution_status = "TRIGGERED"
            else:
                execution.execution_status = "SKIPPED"
            
            execution.execution_time_ms = (time.time() - start_time) * 1000
            await self.db.commit()
            
            return {
                "execution_id": str(execution.execution_id),
                "rule_matched": rule_matched,
                "execution_status": execution.execution_status,
                "execution_time_ms": execution.execution_time_ms
            }
        
        except Exception as e:
            execution.execution_status = "ERROR"
            execution.error_message = str(e)
            execution.execution_time_ms = (time.time() - start_time) * 1000
            await self.db.commit()
            return {
                "error": str(e),
                "execution_status": "ERROR"
            }

    async def _execute_actions(
        self,
        rule: MdClinicalRule,
        context: RuleEvaluationContext,
        execution: MdRuleExecution
    ) -> Dict[str, Any]:
        """Execute actions defined in the rule."""
        actions = rule.action_config.get("actions", [])
        executed_actions = []
        
        for action in actions:
            action_type = action.get("type")
            action_data = action.get("data", {})
            
            if action_type == "log":
                executed_actions.append({
                    "type": "log",
                    "message": action_data.get("message"),
                    "status": "executed"
                })
            elif action_type == "create_task":
                executed_actions.append({
                    "type": "create_task",
                    "task_type": action_data.get("task_type"),
                    "status": "executed"
                })
            elif action_type == "send_notification":
                executed_actions.append({
                    "type": "send_notification",
                    "recipient": action_data.get("recipient"),
                    "status": "executed"
                })
            # Add more action types as needed
        
        return {"actions": executed_actions}

    async def _create_alert(
        self,
        rule: MdClinicalRule,
        execution: MdRuleExecution,
        context: RuleEvaluationContext
    ) -> MdRuleAlert:
        """Create an alert from rule execution."""
        alert_config = rule.action_config.get("alert", {})
        
        alert = MdRuleAlert(
            execution_id=execution.execution_id,
            rule_id=rule.rule_id,
            patient_id=context.patient_id,
            encounter_id=context.encounter_id,
            alert_title=alert_config.get("title", f"Rule Alert: {rule.rule_name}"),
            alert_message=alert_config.get("message", "Clinical rule triggered"),
            severity=rule.severity,
            alert_type=rule.rule_category,
            suggested_action=alert_config.get("suggested_action"),
            action_required=alert_config.get("action_required", True),
            expires_at=datetime.utcnow() + timedelta(hours=24) if alert_config.get("expires_hours") else None
        )
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def evaluate_rules_for_trigger(
        self,
        trigger_type: RuleTriggerType,
        context: RuleEvaluationContext
    ) -> List[Dict[str, Any]]:
        """Evaluate all active rules for a given trigger type."""
        # Get active rules for the trigger type
        now = datetime.utcnow()
        query = select(MdClinicalRule).where(
            and_(
                MdClinicalRule.trigger_type == trigger_type,
                MdClinicalRule.status == RuleStatus.ACTIVE,
                or_(
                    MdClinicalRule.effective_from.is_(None),
                    MdClinicalRule.effective_from <= now
                ),
                or_(
                    MdClinicalRule.effective_to.is_(None),
                    MdClinicalRule.effective_to >= now
                )
            )
        ).order_by(desc(MdClinicalRule.priority))
        
        result = await self.db.execute(query)
        rules = result.scalars().all()
        
        results = []
        for rule in rules:
            try:
                result = await self.execute_rule(rule.rule_id, context)
                results.append(result)
            except Exception as e:
                results.append({
                    "rule_id": str(rule.rule_id),
                    "error": str(e)
                })
        
        return results

    async def get_patient_alerts(
        self,
        patient_id: uuid.UUID,
        encounter_id: Optional[uuid.UUID] = None,
        active_only: bool = True
    ) -> List[MdRuleAlert]:
        """Get alerts for a patient."""
        conditions = [MdRuleAlert.patient_id == patient_id]
        
        if encounter_id:
            conditions.append(MdRuleAlert.encounter_id == encounter_id)
        
        if active_only:
            conditions.append(MdRuleAlert.acknowledged == False)
            conditions.append(MdRuleAlert.dismissed == False)
        
        query = select(MdRuleAlert).where(
            and_(*conditions)
        ).order_by(desc(MdRuleAlert.created_at))
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def acknowledge_alert(
        self,
        alert_id: uuid.UUID,
        acknowledged_by: str
    ) -> Optional[MdRuleAlert]:
        """Acknowledge an alert."""
        query = select(MdRuleAlert).where(MdRuleAlert.alert_id == alert_id)
        result = await self.db.execute(query)
        alert = result.scalar_one_or_none()
        
        if not alert:
            return None
        
        alert.acknowledged = True
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def dismiss_alert(
        self,
        alert_id: uuid.UUID,
        dismissed_by: str
    ) -> Optional[MdRuleAlert]:
        """Dismiss an alert."""
        query = select(MdRuleAlert).where(MdRuleAlert.alert_id == alert_id)
        result = await self.db.execute(query)
        alert = result.scalar_one_or_none()
        
        if not alert:
            return None
        
        alert.dismissed = True
        alert.dismissed_by = dismissed_by
        alert.dismissed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(alert)
        return alert
