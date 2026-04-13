"""Endpoint Registry for QA Module Testing."""
from typing import Dict, List, Optional
from fastapi import FastAPI


class EndpointRegistry:
    """Registry for discovering and managing API endpoints by module."""
    
    def __init__(self):
        self._endpoints: Dict[str, List[str]] = {}
        self._app: Optional[FastAPI] = None
    
    def register_app(self, app: FastAPI):
        """Register the FastAPI app to discover routes."""
        self._app = app
        self._discover_endpoints()
    
    def _discover_endpoints(self):
        """Auto-discover all routes and group by module."""
        if not self._app:
            return
        
        # Group routes by their prefix/module
        for route in self._app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                # Skip the QA routes themselves
                if '/qa/' in route.path:
                    continue
                    
                # Extract module from path
                module = self._extract_module(route.path)
                if module:
                    if module not in self._endpoints:
                        self._endpoints[module] = []
                    self._endpoints[module].append({
                        'path': route.path,
                        'methods': list(route.methods)
                    })
    
    def _extract_module(self, path: str) -> Optional[str]:
        """Extract module name from route path."""
        # Map paths to module names
        path = path.lower()
        
        if '/auth/' in path or path.startswith('/auth'):
            return 'auth'
        elif '/patients/' in path or path.startswith('/patients'):
            return 'patients'
        elif '/encounters/' in path or path.startswith('/encounters'):
            return 'patients'
        elif '/opd/' in path or path.startswith('/opd'):
            return 'opd'
        elif '/ipd/' in path or path.startswith('/ipd'):
            return 'ipd'
        elif '/er/' in path or path.startswith('/er'):
            return 'er'
        elif '/lab/' in path or path.startswith('/lab'):
            return 'lab'
        elif '/radiology/' in path or path.startswith('/radiology'):
            return 'radiology'
        elif '/pharmacy/' in path or path.startswith('/pharmacy'):
            return 'pharmacy'
        elif '/inventory/' in path or path.startswith('/inventory'):
            return 'inventory'
        elif '/billing/' in path or path.startswith('/billing'):
            return 'billing'
        elif '/ot/' in path or path.startswith('/ot'):
            return 'ot'
        elif '/scheduling/' in path or path.startswith('/scheduling'):
            return 'opd'
        elif '/doctor_desk/' in path or path.startswith('/doctor_desk'):
            return 'clinical'
        elif '/nursing/' in path or path.startswith('/nursing'):
            return 'clinical'
        elif '/wards/' in path or path.startswith('/wards'):
            return 'ipd'
        elif '/blood_bank/' in path or path.startswith('/blood_bank'):
            return 'lab'
        elif '/communication/' in path or path.startswith('/communication'):
            return 'clinical'
        elif '/diagnostics/' in path or path.startswith('/diagnostics'):
            return 'lab'
        elif '/procurement/' in path or path.startswith('/procurement'):
            return 'inventory'
        elif '/kiosk/' in path or path.startswith('/kiosk'):
            return 'opd'
        elif '/smart_queue/' in path or path.startswith('/smart_queue'):
            return 'opd'
        elif '/triage/' in path or path.startswith('/triage'):
            return 'opd'
        elif '/tasks/' in path or path.startswith('/tasks'):
            return 'clinical'
        elif '/orders/' in path or path.startswith('/orders'):
            return 'clinical'
        elif '/analytics/' in path or path.startswith('/analytics'):
            return 'admin'
        elif '/audit/' in path or path.startswith('/audit'):
            return 'admin'
        elif '/files/' in path or path.startswith('/files'):
            return 'admin'
        elif '/notifications/' in path or path.startswith('/notifications'):
            return 'admin'
        elif '/config/' in path or path.startswith('/config'):
            return 'admin'
        elif '/tenants/' in path or path.startswith('/tenants'):
            return 'admin'
        elif '/health' in path:
            return 'system'
        
        return None
    
    def get_modules(self) -> List[str]:
        """Get all registered modules."""
        return list(self._endpoints.keys())
    
    def get_module_endpoints(self, module: str) -> List[Dict]:
        """Get all endpoints for a specific module."""
        return self._endpoints.get(module, [])
    
    def get_all_endpoints(self) -> Dict[str, List[Dict]]:
        """Get all endpoints grouped by module."""
        return self._endpoints
    
    def get_endpoint_count(self, module: str) -> int:
        """Get the count of endpoints for a module."""
        return len(self._endpoints.get(module, []))


# Global registry instance
endpoint_registry = EndpointRegistry()
