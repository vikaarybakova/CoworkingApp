from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.models import Booking, Coworking
from app.schemas import BookingCreate, BookingOut

router = APIRouter(prefix="/api", tags=["bookings"])


@router.get("/bookings", response_model=List[BookingOut])
def get_bookings(
    user_id: int = 1,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Booking).filter(Booking.user_id == user_id)
    if status:
        query = query.filter(Booking.status == status)
    bookings = query.order_by(Booking.date.desc(), Booking.start_time.desc()).all()
    return bookings


@router.post("/bookings", response_model=BookingOut)
def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    # Проверяем коворкинг
    coworking = db.query(Coworking).filter(Coworking.id == booking.coworking_id).first()
    if not coworking:
        raise HTTPException(status_code=404, detail="Коворкинг не найден")

    # Рассчитываем стоимость
    # Рассчитываем стоимость
    total_price = 0.0

    from app.models import Space

    # Берём открытое пространство (open_space) или любое активное
    space = db.query(Space).filter(
        Space.coworking_id == booking.coworking_id,
        Space.is_active == True,
        Space.price_per_hour.isnot(None)
    ).order_by(Space.price_per_hour).first()

    if space:
        print(f"DEBUG: space found: {space.name}, price_per_hour={space.price_per_hour}")

        start_parts = booking.start_time.split(":")
        end_parts = booking.end_time.split(":")

        start_h = int(start_parts[0])
        end_h = int(end_parts[0])
        hours = end_h - start_h if end_h > start_h else 1

        total_price = float(space.price_per_hour) * hours
        print(f"DEBUG: hours={hours}, total_price={total_price}")
    else:
        print(f"DEBUG: no space found for coworking_id={booking.coworking_id}")

    # Создаём бронирование
    db_booking = Booking(
        user_id=1,
        coworking_id=booking.coworking_id,
        space_id=booking.space_id,
        date=booking.date,
        start_time=booking.start_time,
        end_time=booking.end_time,
        total_price=total_price,
        promo_code=booking.promo_code,
        status="pending"
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking


@router.put("/bookings/{booking_id}/cancel")
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    booking.status = "cancelled"
    db.commit()
    return {"message": "Бронирование отменено", "booking_id": booking_id}