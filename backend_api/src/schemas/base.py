from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel as PydBaseModel
from pydantic import ConfigDict


class IDSchema(PydBaseModel):
    """Base schema providing an id field."""
    id: str

    model_config = ConfigDict(from_attributes=True)


class TimestampedSchema(PydBaseModel):
    """Base schema providing created_at and updated_at timestamps."""
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
