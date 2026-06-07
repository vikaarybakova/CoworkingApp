from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date
from app.database import get_db
from app.models import Coworking, Space, Booking
from app.schemas import SpaceOut, CoworkingDetail
from fastapi import Form

router = APIRouter(prefix="/api", tags=["coworkings"])


@router.get("/coworkings")
def get_coworkings(
    metro: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Coworking)

    if metro:
        query = query.filter(Coworking.metro_station.ilike(f"%{metro}%"))
    if search:
        query = query.filter(
            (Coworking.name.ilike(f"%{search}%")) |
            (Coworking.description.ilike(f"%{search}%"))
        )

    coworkings = query.all()

    result = []

    for coworking in coworkings:
        min_price_value = db.query(func.min(Space.price_per_hour)).filter(
            Space.coworking_id == coworking.id,
            Space.is_active == True
        ).scalar()

        min_price_float = float(min_price_value) if min_price_value else None

        if min_price is not None and (min_price_float is None or min_price_float < min_price):
            continue
        if max_price is not None and (min_price_float is None or min_price_float > max_price):
            continue

        total_capacity = db.query(func.sum(Space.capacity)).filter(
            Space.coworking_id == coworking.id,
            Space.is_active == True
        ).scalar() or 1

        today = date.today()

        booked = db.query(func.count(Booking.id)).filter(
            Booking.coworking_id == coworking.id,
            Booking.date == today,
            Booking.status.in_(["confirmed", "pending"])
        ).scalar() or 0

        occupancy_percent = round((booked / total_capacity) * 100, 1)

        occupancy_status = "low" if occupancy_percent < 50 \
            else ("medium" if occupancy_percent < 80 else "high")
        result.append({
            "id": coworking.id,
            "name": coworking.name,
            "description": coworking.description,
            "address": coworking.address,
            "metro_station": coworking.metro_station,
            "latitude": str(coworking.latitude) if coworking.latitude else None,
            "longitude": str(coworking.longitude) if coworking.longitude else None,
            "phone": coworking.phone,
            "email": coworking.email,
            "website": coworking.website,
            "working_hours": coworking.working_hours,
            "rating": str(coworking.rating) if coworking.rating else None,
            "min_price": min_price_float,
            "occupancy_percent": occupancy_percent,
            "occupancy_status": occupancy_status
        })
    return result



@router.get("/coworkings/{coworking_id}/spaces")
def get_coworking_spaces(coworking_id: int, db: Session = Depends(get_db)):
    spaces = db.query(Space).filter(
        Space.coworking_id == coworking_id,
        Space.is_active == True
    ).all()

    if not spaces:
        raise HTTPException(status_code=404, detail="Пространства не найдены")

    result = []
    for space in spaces:
        result.append({
            "id": space.id,
            "name": space.name,
            "type": space.type.value if space.type else "open_space",
            "price_per_hour": float(space.price_per_hour) if space.price_per_hour else 0.0,
            "price_per_day": float(space.price_per_day) if space.price_per_day else None,
            "price_per_month": float(space.price_per_month) if space.price_per_month else None,
            "capacity": space.capacity,
            "description": space.description,
            "is_active": space.is_active
        })

    return result



@router.get("/coworkings/{coworking_id}")
def get_coworking_detail(coworking_id: int, db: Session = Depends(get_db)):
    coworking = db.query(Coworking).filter(Coworking.id == coworking_id).first()

    if not coworking:
        raise HTTPException(status_code=404, detail="Коворкинг не найден")

    photos = [f"http://45.142.36.234:8000{photo.photo_url}" for photo in coworking.photos]

    spaces = [
        SpaceOut(
            id=space.id,
            name=space.name,
            type=space.type.value if space.type else "open_space",
            capacity=space.capacity,
            price_per_hour=float(space.price_per_hour) if space.price_per_hour else None,
            price_per_day=float(space.price_per_day) if space.price_per_day else None,
            price_per_month=float(space.price_per_month) if space.price_per_month else None,
            description=space.description,
            is_active=space.is_active
        )
        for space in coworking.spaces
    ]

    total_capacity = db.query(func.sum(Space.capacity)).filter(
        Space.coworking_id == coworking_id,
        Space.is_active == True
    ).scalar() or 1

    today = date.today()
    booked = db.query(func.count(Booking.id)).filter(
        Booking.coworking_id == coworking_id,
        Booking.date == today,
        Booking.status.in_(["confirmed", "pending"])
    ).scalar() or 0

    occupancy_percent = round((booked / total_capacity) * 100, 1)

    return CoworkingDetail(
        id=coworking.id,
        name=coworking.name,
        description=coworking.description,
        address=coworking.address,
        metro_station=coworking.metro_station,
        latitude=str(coworking.latitude) if coworking.latitude else None,
        longitude=str(coworking.longitude) if coworking.longitude else None,
        phone=coworking.phone,
        email=coworking.email,
        website=coworking.website,
        working_hours=coworking.working_hours,
        rating=str(coworking.rating) if coworking.rating else None,
        photos=photos,
        amenities=[],
        spaces=spaces
    )


@router.get("/coworkings/{coworking_id}/occupancy")
def get_coworking_occupancy(coworking_id: int, db: Session = Depends(get_db)):
    coworking = db.query(Coworking).filter(Coworking.id == coworking_id).first()
    if not coworking:
        raise HTTPException(status_code=404, detail="Коворкинг не найден")

    total_capacity = db.query(func.sum(Space.capacity)).filter(
        Space.coworking_id == coworking_id,
        Space.is_active == True
    ).scalar() or 1

    today = date.today()
    booked = db.query(func.count(Booking.id)).filter(
        Booking.coworking_id == coworking_id,
        Booking.date == today,
        Booking.status.in_(["confirmed", "pending"])
    ).scalar() or 0

    occupancy_percent = round((booked / total_capacity) * 100, 1)

    if occupancy_percent < 50:
        status = "low"
        status_text = "Много свободных мест"
    elif occupancy_percent < 80:
        status = "medium"
        status_text = "Средняя загрузка"
    else:
        status = "high"
        status_text = "Мало свободных мест"

    return {
        "coworking_id": coworking_id,
        "total_capacity": total_capacity,
        "booked": booked,
        "free": total_capacity - booked,
        "occupancy_percent": occupancy_percent,
        "status": status,
        "status_text": status_text
    }



@router.get("/spaces/{space_id}")
def get_space_detail(space_id: int, db: Session = Depends(get_db)):
    space = db.query(Space).filter(Space.id == space_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="Пространство не найдено")
    return space

