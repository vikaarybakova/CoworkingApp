from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time
from decimal import Decimal


# --- Схемы пользователей ---
class UserCreate(BaseModel):
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class UserOut(BaseModel):
    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# --- Схемы коворкингов ---
class CoworkingOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    address: str
    metro_station: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    working_hours: Optional[str] = None
    rating: Optional[Decimal] = None
    min_price: Optional[float] = None
    occupancy_percent: Optional[float] = None
    occupancy_status: Optional[str] = None

    class Config:
        from_attributes = True


class CoworkingDetail(CoworkingOut):
    photos: List[str] = []
    amenities: List[str] = []
    spaces: List['SpaceOut'] = []


# --- Схемы пространств ---
class SpaceOut(BaseModel):
    id: int
    name: str
    type: str
    capacity: int
    price_per_hour: Optional[Decimal] = None
    price_per_day: Optional[Decimal] = None
    price_per_month: Optional[Decimal] = None
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


# --- Схемы бронирований ---
class BookingCreate(BaseModel):
    coworking_id: int
    space_id: Optional[int] = None
    workspace_id: Optional[int] = None
    date: date
    start_time: str
    end_time: str
    promo_code: Optional[str] = None


class BookingOut(BaseModel):
    id: int
    user_id: int
    coworking_id: int
    space_id: Optional[int] = None
    date: date
    start_time: time
    end_time: time
    status: str
    total_price: Optional[Decimal] = None

    class Config:
        from_attributes = True