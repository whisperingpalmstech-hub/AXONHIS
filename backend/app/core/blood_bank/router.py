from fastapi import APIRouter

from .blood_components.router import router as components_router
from .blood_inventory.router import router as inventory_router
from .donors.router import router as donors_router
from .blood_units.router import router as units_router
from .transfusion_orders.router import router as orders_router
from .compatibility_tests.router import router as compatibility_router
from .transfusions.router import router as transfusions_router
from .transfusion_reactions.router import router as reactions_router

router = APIRouter(prefix="/blood-bank", tags=["Blood Bank"])

router.include_router(components_router, prefix="/components")
router.include_router(inventory_router, prefix="/storage-units")
router.include_router(donors_router, prefix="/donors")
router.include_router(units_router, prefix="/inventory")
router.include_router(orders_router, prefix="/orders")
# The requirements also specified: 
# POST /blood-bank/crossmatch
# POST /blood-bank/allocate (handled on /orders/{id}/allocations)
# POST /blood-bank/transfusion
# POST /blood-bank/reaction
router.include_router(compatibility_router, prefix="/crossmatch")
router.include_router(transfusions_router, prefix="/transfusion")
router.include_router(reactions_router, prefix="/reaction")
