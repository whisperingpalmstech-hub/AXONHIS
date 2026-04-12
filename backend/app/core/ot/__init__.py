# Import all OT models so SQLAlchemy can resolve string-based relationships
from app.core.ot.operating_rooms.models import OperatingRoom  # noqa: F401
from app.core.ot.surgical_procedures.models import SurgicalProcedure  # noqa: F401
from app.core.ot.surgery_schedule.models import SurgerySchedule  # noqa: F401
from app.core.ot.surgical_teams.models import SurgicalTeam  # noqa: F401
from app.core.ot.anesthesia_records.models import AnesthesiaRecord  # noqa: F401
from app.core.ot.surgery_events.models import SurgeryEvent  # noqa: F401
from app.core.ot.surgery_notes.models import SurgeryNote  # noqa: F401
from app.core.ot.postoperative_events.models import PostoperativeEvent  # noqa: F401
