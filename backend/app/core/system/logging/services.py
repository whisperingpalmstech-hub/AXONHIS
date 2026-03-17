import logging
import uuid
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import SystemLog
from .schemas import LogCreate

class CentralLogger:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Set up a python logger as well for stdout
        self.logger = logging.getLogger("axonhis-system")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    async def log(self, level: str, service_name: str, message: str, 
                  request_id: Optional[str] = None, user_id: Optional[str] = None, 
                  context: Optional[Dict[str, Any]] = None) -> SystemLog:
        # DB log
        sys_log = SystemLog(
            level=level.upper(),
            service_name=service_name,
            message=message,
            request_id=request_id,
            user_id=user_id,
            context=context or {}
        )
        self.db.add(sys_log)
        await self.db.flush()

        # Stdout log
        log_msg = f"[{service_name}] [Req:{request_id}] [User:{user_id}] {message} | ctx:{context}"
        if level.upper() == "INFO":
            self.logger.info(log_msg)
        elif level.upper() == "WARNING":
            self.logger.warning(log_msg)
        elif level.upper() == "ERROR":
            self.logger.error(log_msg)
        elif level.upper() == "CRITICAL":
            self.logger.critical(log_msg)
            
        return sys_log
        
    async def get_logs(self, limit: int = 100, skip: int = 0):
        result = await self.db.execute(
            select(SystemLog).order_by(SystemLog.timestamp.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
