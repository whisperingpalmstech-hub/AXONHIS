import uuid
from sqlalchemy import String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SurgicalProcedure(Base):
    __tablename__ = "surgical_procedures"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    procedure_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    procedure_name: Mapped[str] = mapped_column(String(200), nullable=False)
    specialty: Mapped[str] = mapped_column(String(100), nullable=False)
    expected_duration: Mapped[int] = mapped_column(Integer, nullable=False) # In minutes
    billing_code: Mapped[str] = mapped_column(String(50), nullable=False)

    def __repr__(self) -> str:
        return f"<SurgicalProcedure code={self.procedure_code} name={self.procedure_name}>"
