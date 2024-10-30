from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String
from sqlalchemy.future import select


# Database setup
DATABASE_URL = "sqlite+aiosqlite:///./blacklist.db"  # Use async SQLite for simplicity
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

Base = declarative_base()

# Blacklist token model
class BlacklistToken(Base):
    __tablename__ = "blacklist_tokens"
    token = Column(String, primary_key=True)

async def init_blacklist_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def add_blacklist_token(token: str) -> bool:
    async with SessionLocal() as session:
        async with session.begin():
            blacklist_token = BlacklistToken(token=token)
            session.add(blacklist_token)
        await session.commit()
    return True

async def is_token_blacklisted(token: str) -> bool:
    async with SessionLocal() as session:
        result = await session.execute(select(BlacklistToken).where(BlacklistToken.token == token))
        blacklisted = result.scalars().first()
        return blacklisted is not None

