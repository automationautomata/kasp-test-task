from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from app import setup
from app.config import AppConfig
from app.handlers import middlewares as mw
from app.handlers import router

config = AppConfig()

db_engine = setup.db_engine(config.db_dsn)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await setup.init_db(db_engine)

    yield

    await setup.db_cleanup(db_engine)


app = FastAPI(lifespan=lifespan)
app.include_router(router)

if config.file_uploading_limit_gb is not None:
    app.add_middleware(
        mw.LimitUploadSize, max_upload_size=config.file_uploading_limit_gb
    )

container = setup.container(config, db_engine)
setup_dishka(container, app)
