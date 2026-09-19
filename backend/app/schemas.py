from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class TicketCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, description="Full customer name")
    customer_email: EmailStr = Field(..., description="Valid customer email address")
    subject: str = Field(..., min_length=1, description="Issue subject")
    description: str = Field(..., min_length=1, description="Detailed problem description")


class TicketCreateResponse(BaseModel):
    ticket_id: str
    created_at: datetime


class TicketListResponse(BaseModel):
    ticket_id: str
    customer_name: str
    subject: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class NoteResponse(BaseModel):
    note_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class TicketDetailResponse(BaseModel):
    ticket_id: str
    customer_name: str
    customer_email: str
    subject: str
    description: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    notes: List[NoteResponse] = []

    class Config:
        from_attributes = True


class TicketUpdate(BaseModel):
    status: str = Field(..., description="Status must be 'Open', 'In Progress', or 'Closed'")
    notes: Optional[str] = Field(default=None, description="Optional note text to append to the ticket")


class TicketUpdateResponse(BaseModel):
    success: bool
    updated_at: datetime
