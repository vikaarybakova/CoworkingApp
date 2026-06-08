from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, update
from typing import Optional
from datetime import date, timedelta
from app.database import get_db
from app.models import Booking, Coworking, Space, Payment, Promotion

router = APIRouter(prefix="/api/admin", tags=["admin"])


def update_expired_bookings(db: Session):
    today = date.today()
    db.execute(
        update(Booking)
        .where(Booking.date < today)
        .where(Booking.status == 'confirmed')
        .values(status='completed')
    )
    db.commit()


@router.get("/bookings")
def get_all_bookings(
        status: Optional[str] = None,
        coworking_id: Optional[int] = None,
        db: Session = Depends(get_db)
):
    update_expired_bookings(db)
    query = db.query(Booking)
    if status:
        query = query.filter(Booking.status == status)
    if coworking_id:
        query = query.filter(Booking.coworking_id == coworking_id)
    bookings = query.order_by(Booking.date.desc(), Booking.start_time.desc()).all()
    return bookings


@router.put("/bookings/{booking_id}/status")
def update_booking_status(booking_id: int, status: str, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    booking.status = status
    db.commit()
    return {"message": f"Статус изменён на: {status}", "id": booking_id}


@router.get("/reports/occupancy")
def get_occupancy_report(
        coworking_id: int,
        days: int = 7,
        db: Session = Depends(get_db)
):
    update_expired_bookings(db)
    total_capacity = db.query(func.sum(Space.capacity)).filter(Space.coworking_id == coworking_id).scalar() or 1

    start_date = date.today() - timedelta(days=days - 1)

    rows = db.query(
        Booking.date,
        func.count(Booking.id).label('booked')
    ).filter(
        Booking.coworking_id == coworking_id,
        Booking.status.in_(["confirmed", "completed"]),
        Booking.date >= start_date
    ).group_by(Booking.date).order_by(Booking.date).all()


    booked_dict = {r[0]: r[1] for r in rows}


    labels = []
    values = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        label = d.strftime('%d.%m')
        labels.append(label)
        booked = booked_dict.get(d, 0)
        values.append(round(booked / total_capacity * 100, 1))

    return {"labels": labels, "values": values}


@router.get("/reports/revenue")
def get_revenue_report(
        coworking_id: int,
        days: int = 30,
        db: Session = Depends(get_db)
):
    update_expired_bookings(db)
    start_date = date.today() - timedelta(days=days)
    total = db.query(func.sum(Payment.amount)).join(Booking).filter(
        Booking.coworking_id == coworking_id,
        Payment.status == "completed",
        Payment.id > 0
    ).scalar() or 0
    return {"total_revenue": float(total)}


@router.get("/reports/revenue/daily")
def get_daily_revenue(
        coworking_id: int,
        days: int = 7,
        db: Session = Depends(get_db)
):
    update_expired_bookings(db)
    start_date = date.today() - timedelta(days=days - 1)


    rows = db.query(
        func.date(Payment.paid_at).label('date'),
        func.sum(Payment.amount).label('total')
    ).join(Booking, Payment.booking_id == Booking.id).filter(
        Booking.coworking_id == coworking_id,
        Payment.status == "completed",
        func.date(Payment.paid_at) >= start_date
    ).group_by(func.date(Payment.paid_at)).order_by(func.date(Payment.paid_at)).all()

    revenue_dict = {r[0]: float(r[1]) for r in rows}

    labels = []
    values = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        labels.append(d.strftime('%d.%m'))
        values.append(revenue_dict.get(d, 0))

    return {"labels": labels, "values": values}

@router.get("/promotions")
def get_promotions(db: Session = Depends(get_db)):
    return db.query(Promotion).all()


@router.post("/promotions/add")
def add_promotion(
        code: str = Form(...),
        discount_percent: int = Form(...),
        valid_until: str = Form(""),
        db: Session = Depends(get_db)
):
    p = Promotion(
        code=code,
        discount_percent=discount_percent,
        valid_from=date.today(),
        valid_until=valid_until if valid_until else None,
        max_uses=100,
        is_active=True
    )
    db.add(p)
    db.commit()
    return {"message": "Промокод создан", "id": p.id}


@router.post("/coworkings/add")
def add_coworking(
        name: str = Form(...),
        address: str = Form(...),
        metro_station: str = Form(""),
        phone: str = Form(""),
        working_hours: str = Form(""),
        description: str = Form(""),
        price_per_hour: float = Form(300.00),
        db: Session = Depends(get_db)
):
    c = Coworking(
        name=name,
        description=description,
        address=address,
        metro_station=metro_station,
        phone=phone,
        working_hours=working_hours
    )
    db.add(c)
    db.commit()
    db.refresh(c)

    space = Space(
        coworking_id=c.id,
        name="Основной зал",
        type="open_space",
        capacity=20,
        price_per_hour=price_per_hour,
        price_per_day=price_per_hour * 5,
        price_per_month=price_per_hour * 66,
        description="Основное пространство",
        is_active=True
    )
    db.add(space)
    db.commit()

    return {"message": "Коворкинг добавлен", "id": c.id}