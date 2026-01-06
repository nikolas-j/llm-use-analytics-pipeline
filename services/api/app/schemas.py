from pydantic import BaseModel, field_validator
from datetime import date


class DateQuery(BaseModel):
    """Schema for date query parameter validation."""
    
    date: str
    
    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate that date is in YYYY-MM-DD format."""
        try:
            # Parse to ensure valid date
            date.fromisoformat(v)
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v
