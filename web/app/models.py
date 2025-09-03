from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Boolean, func, Index

class Base(DeclarativeBase):
    pass

class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    
    # Address fields
    street: Mapped[str | None] = mapped_column(String(120), nullable=True)
    house_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    
    course_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    paid: Mapped[bool]  = mapped_column(Boolean, nullable=False, default=False)   # mapped auf TINYINT(1)
    payment_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Add indexes for better query performance
    __table_args__ = (
        Index('idx_email', 'email'),  # For login/lookup queries
        Index('idx_created_at', 'created_at'),  # For sorting by registration date
        Index('idx_paid', 'paid'),  # For filtering paid/unpaid participants
        Index('idx_course_name', 'course_name'),  # For filtering by course
    )
