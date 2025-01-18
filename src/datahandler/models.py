from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship
from sqlalchemy.dialects.mysql import BIGINT
from typing import Optional, List
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Sequence,
    Float,
    Table,
    UniqueConstraint
)
import datetime

base = declarative_base()

alternatives_table = Table(
    "alternative",
    base.metadata,
    Column("product_id", ForeignKey("product.ean_id"), primary_key=True),
    Column("alternative_id", ForeignKey("product.ean_id"), primary_key=True),
    UniqueConstraint('product_id', 'alternative_id', name='unique_alternative')
)

class Unit(base):
    """
    Stores existing package sizing units
    """
    __tablename__ = 'unit'
    name = Column(String(7), primary_key=True)

class ProductPage(base):
    """
    Stores the direct webpage to a product
    """
    __tablename__ = 'productpage'
    ean_id = mapped_column(ForeignKey("product.ean_id"), primary_key=True)
    ean: Mapped["Product"] = relationship()
    shop_id = mapped_column(ForeignKey("shop.id"), primary_key=True)
    shop: Mapped["Shop"] = relationship()
    url = Column(String(255))
    
class Product(base):
    """
    Stores Products identified by their EAN
    """
    __tablename__                       = 'product'
    ean_id                              = Column(BIGINT(unsigned=True), primary_key=True)
    name                                = Column(String(255))
    description                         = Column(String(1023), nullable=True)
    amount                              = Column(Float)
    unit_id                             = mapped_column(ForeignKey("unit.name"))
    unit: Mapped["Unit"]                = relationship()
    image                               = Column(String(255), nullable=True)
    prices: Mapped[List["Price"]]       = relationship(back_populates="ean")
    alternatives: Mapped[List["Product"]] = relationship(
        secondary=alternatives_table,
        primaryjoin=ean_id==alternatives_table.c.product_id,
        secondaryjoin=ean_id==alternatives_table.c.alternative_id,
        backref="alternative_of"
    )

class Price(base):
    """
    Stores Prices associated with Products
    """
    __tablename__                       = 'price'
    id: Mapped[int] = \
        mapped_column(primary_key=True)
    ean_id = \
        Column(BIGINT(unsigned=True), ForeignKey("product.ean_id"))
    ean: Mapped["Product"] = \
        relationship(back_populates="prices")
    value = Column(Float)
    shop_id: Mapped[int] = \
        mapped_column(ForeignKey("shop.id"))
    shop: Mapped["Shop"] = relationship(back_populates="prices")
    date = \
        Column(DateTime, default=datetime.datetime.now)

class Shop(base):
    """
    Stores Shops
    """
    __tablename__                               = 'shop'
    id                                          = \
        Column(Integer, primary_key=True)
    parent_id: Mapped[Optional[int]]            = \
        mapped_column(ForeignKey("shop.id"), nullable=True)
    children: Mapped[List["Shop"]]              = \
        relationship("Shop", backref=backref('parent', remote_side=[id]))
    prices: Mapped[List["Price"]]       = relationship(back_populates="shop")
    name                                = Column(String(255))
    address                             = Column(String(255))
    url                                 = Column(String(255))
    long                                = Column(Float)
    lat                                 = Column(Float)
