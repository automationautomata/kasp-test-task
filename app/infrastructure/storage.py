import pickle

from sqlalchemy import Column, Integer, LargeBinary, String, delete, insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.services.ports import LemmasStatistics, StatisticsStorageError


class Base(DeclarativeBase):
    pass


class LemmaCountsModel(Base):
    __tablename__ = "lemma_counts"

    group = Column(String, primary_key=True, nullable=False)
    group_serial_number = Column(Integer, primary_key=True, nullable=False)
    counts = Column(LargeBinary, nullable=False)
    """
    хранит бинарно сериализованный
    {"counts": stat.lemmas_counts, "is_line_ends": stat.is_line_ends} 
    """


class DBStatisticsStorage:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]):
        self.sessionmaker = sessionmaker

    async def save(self, key: str, stat: LemmasStatistics):
        bindata = pickle.dumps(
            {"counts": stat.lemmas_counts, "is_line_ends": stat.is_line_ends}
        )
        try:
            async with self.sessionmaker() as session:
                stmt = insert(LemmaCountsModel).values(
                    [dict(group=key, group_serial_number=stat.ind, counts=bindata)]
                )

                await session.execute(stmt)
                await session.commit()
        except SQLAlchemyError as e:
            raise StatisticsStorageError() from e

    async def get(self, key: str) -> list[LemmasStatistics]:
        try:
            async with self.sessionmaker() as session:
                stmt = (
                    select(LemmaCountsModel)
                    .where(LemmaCountsModel.group == key)
                    .order_by(LemmaCountsModel.group_serial_number)
                )
                result = await session.execute(stmt)
                rows = result.scalars().all()
                stats: list[LemmasStatistics] = [None] * len(rows)

                for i, row in enumerate(rows):
                    payload = pickle.loads(row.counts)
                    stats[i] = LemmasStatistics(
                        ind=row.group_serial_number,
                        lemmas_counts=payload.get("counts", {}),
                        is_line_ends=payload.get("is_line_ends", False),
                    )

                if not rows:
                    return stats

                delete_stmt = delete(LemmaCountsModel).where(
                    LemmaCountsModel.group == key
                )
                await session.execute(delete_stmt)
                await session.commit()

            return stats
        except SQLAlchemyError as e:
            raise StatisticsStorageError() from e

    async def cleanup(self, key: str):
        try:
            async with self.sessionmaker() as session:
                delete_stmt = delete(LemmaCountsModel).where(
                    LemmaCountsModel.group == key
                )
                await session.execute(delete_stmt)
                await session.commit()
        except SQLAlchemyError as e:
            raise StatisticsStorageError() from e
