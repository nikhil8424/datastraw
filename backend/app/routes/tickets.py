from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import (
    TicketCreate,
    TicketCreateResponse,
    TicketListResponse,
    TicketDetailResponse,
    TicketUpdate,
    TicketUpdateResponse,
)
from .. import crud

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])


@router.post(
    "",
    response_model=TicketCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new support ticket"
)
def create_ticket(
    ticket_in: TicketCreate,
    db: Session = Depends(get_db)
):
    ticket = crud.create_ticket(db=db, ticket_in=ticket_in)
    return TicketCreateResponse(
        ticket_id=ticket.ticket_id,
        created_at=ticket.created_at
    )


@router.get(
    "",
    response_model=List[TicketListResponse],
    summary="List all tickets with optional status and search filtering"
)
def list_tickets(
    status: Optional[str] = Query(None, description="Filter by status: Open, In Progress, Closed"),
    search: Optional[str] = Query(None, description="Case-insensitive search across name, id, email, subject, description"),
    db: Session = Depends(get_db)
):
    tickets = crud.get_tickets(db=db, status=status, search=search)
    return tickets


@router.get(
    "/{ticket_id}",
    response_model=TicketDetailResponse,
    summary="Get ticket details and associated timeline notes"
)
def get_ticket_details(
    ticket_id: str,
    db: Session = Depends(get_db)
):
    ticket = crud.get_ticket(db=db, ticket_id=ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with ID '{ticket_id}' not found"
        )
    return ticket


@router.put(
    "/{ticket_id}",
    response_model=TicketUpdateResponse,
    summary="Update ticket status and optionally append a note"
)
def update_ticket(
    ticket_id: str,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db)
):
    try:
        updated_ticket = crud.update_ticket(db=db, ticket_id=ticket_id, ticket_update=ticket_update)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not updated_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with ID '{ticket_id}' not found"
        )

    return TicketUpdateResponse(
        success=True,
        updated_at=updated_ticket.updated_at
    )
