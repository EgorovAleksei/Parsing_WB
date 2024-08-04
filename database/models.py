import enum
from typing import Annotated, Any, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum
from sqlalchemy import Enum as PgEnum

intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]


# js = Annotated[JSON]
# created_at = Annotated[DateTime, mapped_column(DateTime, server_default=func.now())]
# updated_at = Annotated[DateTime, mapped_column(DateTime, server_default=func.now(), onupdate=func.now())]


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    type_annotation_map = {list[dict[Any, Any]]: JSONB, dict[Any, Any]: JSONB}

    repr_cols_num = 3
    repr_cols = tuple()

    def __repr__(self):
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")
        return f"<{self.__class__.__name__} {', '.join(cols)}"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[intpk]
    # wb_id: Mapped[int]
    parent: Mapped[int] = mapped_column(nullable=True, default=None)
    name: Mapped[str]
    seo: Mapped[str] = mapped_column(nullable=True)
    url: Mapped[str] = mapped_column(nullable=True)
    shard: Mapped[str] = mapped_column(nullable=True)
    query: Mapped[str] = mapped_column(nullable=True)
    childs: Mapped[bool] = mapped_column(default=True)
    published: Mapped[bool] = mapped_column(default=True)
    sub_category: Mapped[list[dict[Any, Any]]] = mapped_column(
        type_=JSONB, nullable=True, default=None
    )
    filter_category: Mapped[bool] = mapped_column(default=True)
    lft: Mapped[int]
    rght: Mapped[int]
    tree_id: Mapped[int]
    level: Mapped[int]


# class Category11(Base):
#     __tablename__ = "category11"
#
#     id: Mapped[intpk]
#     # wb_id: Mapped[int]
#     parent: Mapped[int] = mapped_column(nullable=True, default=None)
#     name: Mapped[str]
#     seo: Mapped[str] = mapped_column(nullable=True)
#     url: Mapped[str] = mapped_column(nullable=True)
#     shard: Mapped[str] = mapped_column(nullable=True)
#     query: Mapped[str] = mapped_column(nullable=True)
#     childs: Mapped[bool] = mapped_column(default=True)
#     published: Mapped[bool] = mapped_column(default=True)
#     sub_category: Mapped[list[dict[Any, Any]]] = mapped_column(
#         type_=JSONB, nullable=True, default=None
#     )
#     filter_category: Mapped[bool] = mapped_column(default=True)


# class CategoryWB(Base):
#     __tablename__ = 'categorywb'
#
#     id: Mapped[intpk]
#     wb_id: Mapped[int]
#     parent: Mapped[int] = mapped_column(nullable=True, default=None)
#     name: Mapped[str]
#     seo: Mapped[str] = mapped_column(nullable=True)
#     url: Mapped[str] = mapped_column(nullable=True)
#     shard: Mapped[str] = mapped_column(nullable=True)
#     query: Mapped[str] = mapped_column(nullable=True)
#     childs: Mapped[bool] = mapped_column(default=True)
#     published: Mapped[bool] = mapped_column(default=True)
#     sub_category: Mapped[list[dict[Any, Any]]] = mapped_column(type_=JSONB, nullable=True, default=None)
#     filter_category: Mapped[bool] = mapped_column(default=True)


class Options(Base):
    __tablename__ = "options"

    id: Mapped[intpk]
    nm_id: Mapped[int] = mapped_column(ForeignKey("product.id", ondelete="CASCADE"))
    card: Mapped[dict[Any, Any]]


class Brand(Base):
    __tablename__ = "brand"

    id: Mapped[intpk]
    name: Mapped[str]


class BrandWB(Base):
    __tablename__ = "brandwb"

    id: Mapped[intpk]
    wb_id: Mapped[int]
    name: Mapped[str]


class Product(Base):
    __tablename__ = "product"

    id: Mapped[intpk]
    # wb_id: Mapped[int]
    name: Mapped[str]
    price: Mapped[int] = mapped_column(default=None)
    quantity: Mapped[int] = mapped_column(default=0)
    brand: Mapped[int | None] = mapped_column(
        ForeignKey("brand.id", onupdate="SET NULL")
    )
    category: Mapped[int] = mapped_column(ForeignKey("category.id", ondelete="CASCADE"))
    root: Mapped[int | None]
    subjectId: Mapped[int | None]
    rating: Mapped[int | None]
    pics: Mapped[dict[Any, Any]]
    price_history: Mapped[list[dict[Any, Any]]] = mapped_column(type_=JSONB)

    repr_cols_num = 3
    repr_cols = ("category", "subjectID", "updated")


# class ProductWB(Base):
#     __tablename__ = 'productwb'
#
#     id: Mapped[intpk]
#     wb_id: Mapped[int]
#     name: Mapped[str]
#     price: Mapped[int] = mapped_column(default=None)
#     quantity: Mapped[int] = mapped_column(default=0)
#     brand: Mapped[int | None] = mapped_column(ForeignKey('brand.id', onupdate='SET NULL'))
#     category: Mapped[int] = mapped_column(ForeignKey('category.id', ondelete='CASCADE'))
#     root: Mapped[int | None]
#     subjectId: Mapped[int | None]
#     rating: Mapped[int | None]
#     pics: Mapped[dict[Any, Any]]
#     price_history: Mapped[list[dict[Any, Any]]] = mapped_column(type_=JSONB)
#
#     repr_cols_num = 3
#     repr_cols = ('category', 'subjectID', 'updated')
