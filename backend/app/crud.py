from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from .models import Ticket, Note
from .schemas import TicketCreate, TicketUpdate

ALLOWED_STATUSES = {"Open", "In Progress", "Closed"}


def generate_next_ticket_id(db: Session) -> str:
    """Generate the next sequential ticket_id in format TKT-001, TKT-002, etc."""
    # Find all ticket_ids to determine the max integer sequence
    tickets = db.query(Ticket.ticket_id).all()
    max_num = 0
    for (t_id,) in tickets:
        if t_id and t_id.startswith("TKT-"):
            try:
                num = int(t_id.split("-")[1])
                if num > max_num:
                    max_num = num
            except (ValueError, IndexError):
                pass
    next_num = max_num + 1
    return f"TKT-{next_num:03d}"


def create_ticket(db: Session, ticket_in: TicketCreate) -> Ticket:
    ticket_id = generate_next_ticket_id(db)
    now = datetime.utcnow()
    db_ticket = Ticket(
        ticket_id=ticket_id,
        customer_name=ticket_in.customer_name.strip(),
        customer_email=ticket_in.customer_email.strip(),
        subject=ticket_in.subject.strip(),
        description=ticket_in.description.strip(),
        status="Open",
        created_at=now,
        updated_at=now,
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def get_tickets(
    db: Session,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> List[Ticket]:
    query = db.query(Ticket)

    if status and status != "All" and status.strip():
        # Match status exactly
        query = query.filter(Ticket.status == status.strip())

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Ticket.customer_name.ilike(term),
                Ticket.ticket_id.ilike(term),
                Ticket.customer_email.ilike(term),
                Ticket.subject.ilike(term),
                Ticket.description.ilike(term),
            )
        )

    return query.order_by(Ticket.id.desc()).all()


def get_ticket(db: Session, ticket_id: str) -> Optional[Ticket]:
    # Case-insensitive lookup for ticket_id
    return db.query(Ticket).filter(func.lower(Ticket.ticket_id) == ticket_id.strip().lower()).first()


def create_note(db: Session, ticket_id: str, note_text: str) -> Note:
    now = datetime.utcnow()
    db_note = Note(
        ticket_id=ticket_id,
        note_text=note_text.strip(),
        created_at=now
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


def update_ticket(db: Session, ticket_id: str, ticket_update: TicketUpdate) -> Optional[Ticket]:
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None

    # Validate status
    if ticket_update.status not in ALLOWED_STATUSES:
        raise ValueError(f"Invalid status '{ticket_update.status}'. Allowed: {', '.join(sorted(ALLOWED_STATUSES))}")

    now = datetime.utcnow()
    db_ticket.status = ticket_update.status
    db_ticket.updated_at = now

    # If note is provided and non-empty, create a note
    if ticket_update.notes and ticket_update.notes.strip():
        db_note = Note(
            ticket_id=db_ticket.ticket_id,
            note_text=ticket_update.notes.strip(),
            created_at=now
        )
        db.add(db_note)

    db.commit()
    db.refresh(db_ticket)
    return db_ticket
