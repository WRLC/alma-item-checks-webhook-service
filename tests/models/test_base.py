"""Test suite for base model"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase

from alma_item_checks_webhook_service.models.base import Base


def test_base_is_declarative_base():
    """Test that Base is a subclass of DeclarativeBase."""
    assert issubclass(Base, DeclarativeBase)


def test_base_can_be_subclassed():
    """Test that Base can be used as a base for other models."""

    class MyModel(Base):
        __tablename__ = "my_model"
        id = Column(Integer, primary_key=True)
        name = Column(String)

    assert hasattr(MyModel, "__tablename__")
    assert MyModel.__tablename__ == "my_model"
    assert "id" in MyModel.__table__.columns
    assert "name" in MyModel.__table__.columns
