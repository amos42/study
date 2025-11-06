import json
from functools import wraps
from typing import Generator

from fastapi import FastAPI
from sqlalchemy import QueuePool
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.ddl import CreateTable

from genai.base.common.logger_support import get_logger
from genai.base.common.query_support import QueryHelper

logger = get_logger(__name__)

Base = declarative_base()

class SQLAlchemy:
    def __init__(self, app: FastAPI = None, database_url: str = None, pool_recycle: int = 900):
        self._database_url = database_url
        self._engine = None
        self._session = None
        if app is not None:
            self.init_app(app, database_url, pool_recycle)

    def init_app(
        self,
        app: FastAPI = None,
        database_url: str = None,
        pool_recycle: int = 900,
        pool_pre_ping: bool = True,
        pool_size: int = 150,
        max_overflow: int = 0,
        connect_args: dict = {},
    ):
        self._database_url = database_url
        self._engine = create_engine(
            database_url,
            echo=True,
            pool_recycle=pool_recycle,
            pool_pre_ping=pool_pre_ping,
            poolclass=QueuePool,
            max_overflow=max_overflow,
            pool_size=pool_size,
            connect_args=connect_args,
            json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False)
        )

        self._session = sessionmaker(autoflush=False, bind=self._engine)

        if app is not None:
            @app.on_event("startup")
            def startup():
                self.startup()

            @app.on_event("shutdown")
            def shutdown():
                self.shutdown()

    def startup(self):
        if self._engine is not None:
            self._engine.connect()
            logger.info("DB connected.")
            logger.debug(f"database_url: {self._database_url}")

    def shutdown(self):
        self._session.close_all()
        self._engine.dispose()
        logger.info("DB disconnected")

    def get_db(self) -> Generator:
        if self._session is None:
            raise Exception("must be called 'init_app'")
        db_session = None
        try:
            db_session = self._session()
            yield db_session
        finally:
            db_session.close()

    @property
    def session(self):
        return self.get_db

    @property
    def engine(self):
        return self._engine

    # noinspection PyUnresolvedReferences

    def create_table(self, checkfirst: bool = True):
        Base.metadata.create_all(bind=self.engine, checkfirst=checkfirst)

    def print_ddl(self):
        for table in Base.metadata.tables.values():
            logger.debug(CreateTable(table).compile(self.engine))

    def init_data_table(self, init_tables: list[str]):
        session = next(self.get_db())
        try:
            for table in Base.metadata.tables.values():
                if table.name in init_tables:
                    session.query(table).delete()
                    session.commit()
        except Exception as e:
            logger.info(f"need transaction rollback by [{e}]")
            if session:
                session.rollback()
                logger.info(f"transaction rollback by [{e}]")

            raise e
        finally:
            session.close()

db = SQLAlchemy()


def inject_transactional_session(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        logger.info(f"transaction begins with {func.__name__}:, {db.engine.pool.status()}")

        implicit_kwargs = {}
        session = kwargs.get("session")
        if not session:
            session = next(db.session())

        if "session" in func.__code__.co_varnames:
            implicit_kwargs["session"] = session

        if "select" not in kwargs and "select" in func.__code__.co_varnames:
            implicit_kwargs["select"] = QueryHelper.get_factory(session)

        try:
            result = func(*args, **kwargs, **implicit_kwargs)

            if session:
                session.commit()

        except Exception as e:
            logger.info(f"need transaction rollback with {func.__name__} by [{e}]")

            if session:
                session.rollback()
                logger.info(f"transaction rollback with {func.__name__} by [{e}]")

            raise e
        finally:
            if session is not None and isinstance(session, Session):
                session.close()
            logger.info(f"transaction ends with {func.__name__}: {db.engine.pool.status()}")
        return result

    return decorated
