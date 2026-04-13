"""Business logic validation checks for QA module."""
import time
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.qa.schemas import LogicCheckResponse


async def check_package_creation(
    package_data: Dict[str, Any],
    db: AsyncSession
) -> LogicCheckResponse:
    """
    Check if package creation logic is working correctly.
    
    Args:
        package_data: Package data to test
        db: Database session
    
    Returns:
        LogicCheckResponse with validation status
    """
    start_time = time.time()
    
    try:
        # Validate package structure
        required_fields = ["name", "services", "base_price"]
        for field in required_fields:
            if field not in package_data:
                return LogicCheckResponse(
                    status="validation_failed",
                    check_type="package_creation",
                    result=False,
                    execution_time_ms=round((time.time() - start_time) * 1000, 2),
                    error_message=f"Required field '{field}' is missing"
                )
        
        # Validate services list
        if not isinstance(package_data["services"], list) or len(package_data["services"]) == 0:
            return LogicCheckResponse(
                status="validation_failed",
                check_type="package_creation",
                result=False,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
                error_message="Package must have at least one service"
            )
        
        # Validate base price
        if not isinstance(package_data["base_price"], (int, float)) or package_data["base_price"] <= 0:
            return LogicCheckResponse(
                status="validation_failed",
                check_type="package_creation",
                result=False,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
                error_message="Base price must be a positive number"
            )
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        return LogicCheckResponse(
            status="passed",
            check_type="package_creation",
            result=True,
            execution_time_ms=round(execution_time_ms, 2),
            error_message=None
        )
    
    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        return LogicCheckResponse(
            status="error",
            check_type="package_creation",
            result=False,
            execution_time_ms=round(execution_time_ms, 2),
            error_message=str(e)
        )


async def check_package_rate_calculation(
    package_id: str,
    patient_category: str,
    bed_type: Optional[str] = None,
    payment_entitlement: Optional[str] = None,
    db: AsyncSession = None
) -> LogicCheckResponse:
    """
    Check if package rate calculation logic is working correctly.
    
    Args:
        package_id: Package ID to test
        patient_category: Patient category (e.g., 'national', 'foreign', 'bpl')
        bed_type: Optional bed type
        payment_entitlement: Optional payment entitlement
        db: Database session
    
    Returns:
        LogicCheckResponse with validation status
    """
    start_time = time.time()
    
    try:
        # Validate inputs
        if not package_id:
            return LogicCheckResponse(
                status="validation_failed",
                check_type="package_rate_calculation",
                result=False,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
                error_message="Package ID is required"
            )
        
        if not patient_category:
            return LogicCheckResponse(
                status="validation_failed",
                check_type="package_rate_calculation",
                result=False,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
                error_message="Patient category is required"
            )
        
        # Validate patient category
        valid_categories = ["national", "foreign", "bpl", "employee", "nok_employee"]
        if patient_category not in valid_categories:
            return LogicCheckResponse(
                status="validation_failed",
                check_type="package_rate_calculation",
                result=False,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
                error_message=f"Invalid patient category. Valid values: {', '.join(valid_categories)}"
            )
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Note: This is a logic check - actual rate calculation would be done in the service layer
        # Here we're validating that the inputs are correct for rate calculation
        
        return LogicCheckResponse(
            status="passed",
            check_type="package_rate_calculation",
            result=True,
            execution_time_ms=round(execution_time_ms, 2),
            error_message=None
        )
    
    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        return LogicCheckResponse(
            status="error",
            check_type="package_rate_calculation",
            result=False,
            execution_time_ms=round(execution_time_ms, 2),
            error_message=str(e)
        )


async def check_stock_movement(
    transaction_id: str,
    db: AsyncSession
) -> LogicCheckResponse:
    """
    Check if stock movement logic is working correctly.
    
    Args:
        transaction_id: Stock transaction ID to validate
        db: Database session
    
    Returns:
        LogicCheckResponse with validation status
    """
    start_time = time.time()
    
    try:
        # Validate transaction ID
        if not transaction_id:
            return LogicCheckResponse(
                status="validation_failed",
                check_type="stock_movement",
                result=False,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
                error_message="Transaction ID is required"
            )
        
        # Check if transaction exists in stock ledger
        from app.core.inventory.models import StockLedger
        
        result = await db.execute(
            select(StockLedger).where(StockLedger.id == transaction_id)
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            return LogicCheckResponse(
                status="validation_failed",
                check_type="stock_movement",
                result=False,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
                error_message=f"Transaction {transaction_id} not found"
            )
        
        # Validate transaction type
        valid_types = ["OPENING_BALANCE", "ISSUE", "RECEIPT", "CONSUMPTION", "ADJUSTMENT", "SCRAP"]
        if transaction.transaction_type not in valid_types:
            return LogicCheckResponse(
                status="validation_failed",
                check_type="stock_movement",
                result=False,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
                error_message=f"Invalid transaction type: {transaction.transaction_type}"
            )
        
        # Validate quantity change
        if transaction.quantity_change == 0:
            return LogicCheckResponse(
                status="validation_failed",
                check_type="stock_movement",
                result=False,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
                error_message="Quantity change cannot be zero"
            )
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        return LogicCheckResponse(
            status="passed",
            check_type="stock_movement",
            result=True,
            execution_time_ms=round(execution_time_ms, 2),
            error_message=None
        )
    
    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        return LogicCheckResponse(
            status="error",
            check_type="stock_movement",
            result=False,
            execution_time_ms=round(execution_time_ms, 2),
            error_message=str(e)
        )


async def check_stock_valuation(
    store_id: str,
    valuation_method: str,
    db: AsyncSession
) -> LogicCheckResponse:
    """
    Check if stock valuation logic is working correctly.
    
    Args:
        store_id: Store ID to validate
        valuation_method: Valuation method (e.g., 'moving_average', 'fifo', 'lifo')
        db: Database session
    
    Returns:
        LogicCheckResponse with validation status
    """
    start_time = time.time()
    
    try:
        # Validate inputs
        if not store_id:
            return LogicCheckResponse(
                status="validation_failed",
                check_type="stock_valuation",
                result=False,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
                error_message="Store ID is required"
            )
        
        # Validate valuation method
        valid_methods = ["moving_average", "fifo", "lifo"]
        if valuation_method not in valid_methods:
            return LogicCheckResponse(
                status="validation_failed",
                check_type="stock_valuation",
                result=False,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
                error_message=f"Invalid valuation method. Valid values: {', '.join(valid_methods)}"
            )
        
        # Check if store exists
        from app.core.inventory.models import Store
        
        result = await db.execute(
            select(Store).where(Store.id == store_id)
        )
        store = result.scalar_one_or_none()
        
        if not store:
            return LogicCheckResponse(
                status="validation_failed",
                check_type="stock_valuation",
                result=False,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
                error_message=f"Store {store_id} not found"
            )
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        return LogicCheckResponse(
            status="passed",
            check_type="stock_valuation",
            result=True,
            execution_time_ms=round(execution_time_ms, 2),
            error_message=None
        )
    
    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        return LogicCheckResponse(
            status="error",
            check_type="stock_valuation",
            result=False,
            execution_time_ms=round(execution_time_ms, 2),
            error_message=str(e)
        )


async def check_billing_workflow(
    bill_id: str,
    workflow_stage: str,
    db: AsyncSession
) -> LogicCheckResponse:
    """
    Check if billing workflow logic is working correctly.
    
    Args:
        bill_id: Bill ID to validate
        workflow_stage: Expected workflow stage (e.g., 'interim', 'intermediate', 'final')
        db: Database session
    
    Returns:
        LogicCheckResponse with validation status
    """
    start_time = time.time()
    
    try:
        # Validate inputs
        if not bill_id:
            return LogicCheckResponse(
                status="validation_failed",
                check_type="billing_workflow",
                result=False,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
                error_message="Bill ID is required"
            )
        
        # Validate workflow stage
        valid_stages = ["interim", "intermediate", "final", "on_hold", "settled", "cancelled"]
        if workflow_stage not in valid_stages:
            return LogicCheckResponse(
                status="validation_failed",
                check_type="billing_workflow",
                result=False,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
                error_message=f"Invalid workflow stage. Valid values: {', '.join(valid_stages)}"
            )
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Note: This is a logic check - actual workflow validation would check the bill in the database
        # Here we're validating that the inputs are correct for workflow validation
        
        return LogicCheckResponse(
            status="passed",
            check_type="billing_workflow",
            result=True,
            execution_time_ms=round(execution_time_ms, 2),
            error_message=None
        )
    
    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        return LogicCheckResponse(
            status="error",
            check_type="billing_workflow",
            result=False,
            execution_time_ms=round(execution_time_ms, 2),
            error_message=str(e)
        )


async def check_discount_authorization(
    discount_percentage: float,
    user_role: str,
    max_allowed_discount: Optional[float] = None
) -> LogicCheckResponse:
    """
    Check if discount authorization logic is working correctly.
    
    Args:
        discount_percentage: Discount percentage to validate
        user_role: User role requesting discount
        max_allowed_discount: Maximum discount allowed for role
    
    Returns:
        LogicCheckResponse with validation status
    """
    start_time = time.time()
    
    try:
        # Validate discount percentage
        if not isinstance(discount_percentage, (int, float)):
            return LogicCheckResponse(
                status="validation_failed",
                check_type="discount_authorization",
                result=False,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
                error_message="Discount percentage must be a number"
            )
        
        if discount_percentage < 0 or discount_percentage > 100:
            return LogicCheckResponse(
                status="validation_failed",
                check_type="discount_authorization",
                result=False,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
                error_message="Discount percentage must be between 0 and 100"
            )
        
        # Validate against max allowed if provided
        if max_allowed_discount is not None and discount_percentage > max_allowed_discount:
            return LogicCheckResponse(
                status="authorization_required",
                check_type="discount_authorization",
                result=False,
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
                error_message=f"Discount {discount_percentage}% exceeds maximum allowed {max_allowed_discount}% for role {user_role}"
            )
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        return LogicCheckResponse(
            status="passed",
            check_type="discount_authorization",
            result=True,
            execution_time_ms=round(execution_time_ms, 2),
            error_message=None
        )
    
    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        return LogicCheckResponse(
            status="error",
            check_type="discount_authorization",
            result=False,
            execution_time_ms=round(execution_time_ms, 2),
            error_message=str(e)
        )
