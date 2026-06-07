from sqlalchemy import Column, Integer, String, Text, DECIMAL, TIMESTAMP, Date, Time, ForeignKey, Enum as SqlEnum, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
import enum


# Перечисления (ENUM)
class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"
    superadmin = "superadmin"


class SpaceType(str, enum.Enum):
    open_space = "open_space"
    private_office = "private_office"
    meeting_room = "meeting_room"
    quiet_zone = "quiet_zone"
    lounge = "lounge"


class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    refunded = "refunded"
    failed = "failed"


class TariffType(str, enum.Enum):
    hourly = "hourly"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    corporate = "corporate"


# Модели таблиц

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    role = Column(SqlEnum(UserRole), default=UserRole.user)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")

    bookings = relationship("Booking", back_populates="user")
    reviews = relationship("Review", back_populates="user")


class Coworking(Base):
    __tablename__ = "coworkings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    address = Column(String(500), nullable=False)
    metro_station = Column(String(255))
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    phone = Column(String(20))
    email = Column(String(255))
    website = Column(String(255))
    working_hours = Column(String(255))
    rating = Column(DECIMAL(3, 2), default=0)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")

    photos = relationship("CoworkingPhoto", back_populates="coworking")
    amenities = relationship("CoworkingAmenity", back_populates="coworking")
    spaces = relationship("Space", back_populates="coworking")
    bookings = relationship("Booking", back_populates="coworking")
    tariffs = relationship("Tariff", back_populates="coworking")
    promotions = relationship("Promotion", back_populates="coworking")
    reviews = relationship("Review", back_populates="coworking")


class CoworkingPhoto(Base):
    __tablename__ = "coworking_photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    coworking_id = Column(Integer, ForeignKey("coworkings.id", ondelete="CASCADE"), nullable=False)
    photo_url = Column(String(500), nullable=False)
    is_main = Column(Boolean, default=False)

    coworking = relationship("Coworking", back_populates="photos")


class Amenity(Base):
    __tablename__ = "amenities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    icon = Column(String(100))


class CoworkingAmenity(Base):
    __tablename__ = "coworking_amenities"

    coworking_id = Column(Integer, ForeignKey("coworkings.id", ondelete="CASCADE"), primary_key=True)
    amenity_id = Column(Integer, ForeignKey("amenities.id", ondelete="CASCADE"), primary_key=True)

    coworking = relationship("Coworking", back_populates="amenities")


class Space(Base):
    __tablename__ = "spaces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    coworking_id = Column(Integer, ForeignKey("coworkings.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(SqlEnum(SpaceType), nullable=False)
    capacity = Column(Integer, nullable=False, default=1)
    price_per_hour = Column(DECIMAL(10, 2))
    price_per_day = Column(DECIMAL(10, 2))
    price_per_month = Column(DECIMAL(10, 2))
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    coworking = relationship("Coworking", back_populates="spaces")
    workspaces = relationship("Workspace", back_populates="space")
    bookings = relationship("Booking", back_populates="space")


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    space_id = Column(Integer, ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50))
    is_active = Column(Boolean, default=True)

    space = relationship("Space", back_populates="workspaces")
    bookings = relationship("Booking", back_populates="workspace")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"))
    space_id = Column(Integer, ForeignKey("spaces.id", ondelete="SET NULL"))
    coworking_id = Column(Integer, ForeignKey("coworkings.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(SqlEnum(BookingStatus), default=BookingStatus.pending)
    total_price = Column(DECIMAL(10, 2))
    promo_code = Column(String(50))
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")

    user = relationship("User", back_populates="bookings")
    workspace = relationship("Workspace", back_populates="bookings")
    space = relationship("Space", back_populates="bookings")
    coworking = relationship("Coworking", back_populates="bookings")
    payment = relationship("Payment", back_populates="booking", uselist=False)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    payment_method = Column(String(50))
    status = Column(SqlEnum(PaymentStatus), default=PaymentStatus.pending)
    transaction_id = Column(String(255))
    paid_at = Column(TIMESTAMP)

    booking = relationship("Booking", back_populates="payment")


class Promotion(Base):
    __tablename__ = "promotions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    discount_percent = Column(Integer, nullable=False)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=False)
    max_uses = Column(Integer)
    used_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    coworking_id = Column(Integer, ForeignKey("coworkings.id", ondelete="SET NULL"))

    coworking = relationship("Coworking", back_populates="promotions")


class Tariff(Base):
    __tablename__ = "tariffs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    coworking_id = Column(Integer, ForeignKey("coworkings.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(DECIMAL(10, 2), nullable=False)
    duration_days = Column(Integer)
    type = Column(SqlEnum(TariffType), nullable=False)
    is_active = Column(Boolean, default=True)

    coworking = relationship("Coworking", back_populates="tariffs")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    coworking_id = Column(Integer, ForeignKey("coworkings.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")

    user = relationship("User", back_populates="reviews")
    coworking = relationship("Coworking", back_populates="reviews")