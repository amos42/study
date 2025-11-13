import unittest
from collections.abc import Generator
from functools import wraps
from typing import Type
from typing import TypeVar

import pytest
from pydantic import BaseModel
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker


class MyDomain(BaseModel):
    item_id: int = 0
    title: str = ""
    contents: str | None


T = TypeVar("T")

def copy(from_object, to_type: Type[T], **kwargs) -> T:
    if from_object is None:
        return None

    rule_dict = from_object.__dict__.copy()
    rule_dict.update(kwargs)

    keys_to_remove = [k for k in rule_dict if k not in to_type.__annotations__ and not hasattr(to_type, k)]
    for k in keys_to_remove:
        del rule_dict[k]
    return to_type(**rule_dict)

class ConverterMixin:
    def convert_to(self, to_class: Type[T], **kwargs) -> T:
        return copy(self, to_class, **kwargs)

    @classmethod
    def convert_from(cls, from_object, **kwargs):
        return copy(from_object, cls, **kwargs)


def inject_transactional_session(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        implicit_kwargs = {}
        session = kwargs.get("session")
        if not session:
            session = next(db.session())
        if "session" in func.__code__.co_varnames:
            implicit_kwargs["session"] = session
        try:
            result = func(*args, **kwargs, **implicit_kwargs)
            if session:
                session.commit()
        except Exception as e:
            if session:
                session.rollback()
            raise e
        finally:
            if session is not None and isinstance(session, Session):
                session.close()
        return result
    return decorated


Base = declarative_base()

class MyTable(Base, ConverterMixin):
    __tablename__ = "my_sample"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    contents = Column(String, nullable=True)

    def to_domain(self) -> MyDomain:
        return self.convert_to(MyDomain, item_id=self.id)

    @classmethod
    def from_domain(cls, domain: MyDomain):  # -> MyTable:
        return cls.convert_from(domain, id=domain.item_id)

class MyRepository:
    @inject_transactional_session
    def create(self, domain: MyDomain, session: Session = None) -> MyDomain:
        # Domain -> table
        table: MyTable = MyTable.from_domain(domain)
        # implement table insert logic
        session.add(table)
        session.flush()
        session.refresh(table)
        domain: MyDomain = table.to_domain()
        return domain

    @inject_transactional_session
    def get_item_list(
        self,
        filter_title: str | None = None,
        session: Session = None,
    ) -> list[MyDomain]:
        # 필터 조건에 맞춰서 쿼리
        query = session.query(MyTable)
        if filter_title:
            query = query.filter(MyTable.title.like(filter_title))
        # total = query.count()

        tables: list[MyTable] = query.all()
        lst: list[MyDomain] = list(map(lambda r: r.to_domain(), tables))

        return lst

class MyDb:
    def __init__(self):
        self._engine = create_engine("sqlite:///:memory:")
        self._session = sessionmaker(autoflush=False, bind=self._engine)

    def create_tables(self):
        Base.metadata.create_all(bind=self._engine, checkfirst=True)

    def shutdown(self):
        self._session.close_all()
        self._engine.dispose()

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

db = MyDb()

#=======================================================


def _make_sample_data(item_id: int = 1) -> MyDomain:
    return MyDomain(
        item_id=item_id,
        title=f"Sample {item_id}",
        contents=f"Sample {item_id}",
    )

def _make_sample_table_data_list(count: int) -> list[MyTable]:
    samples = []
    for i in range(1, count + 1):
        record = MyTable.from_domain(_make_sample_data(i))
        samples.append(record)
    return samples

class TestDatabaseMyRepository(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.repository = MyRepository()

    def setUp(self):
        self.samples = _make_sample_table_data_list(10)
        db.create_tables()
        self.add_one_record()

    def tearDown(self):
        db.shutdown()

    def add_one_record(self):
        session: Session = next(db.session())
        session.add(MyTable.from_domain(_make_sample_data(1)))
        session.commit()

    def test_data_exchange(self):
        access_data = _make_sample_data()

        access_table: MyTable = MyTable.from_domain(access_data)

        self.assertIsInstance(access_table, MyTable)
        self.assertEqual(access_table.id, access_data.item_id)
        self.assertEqual(access_table.title, access_data.title)
        self.assertEqual(access_table.contents, access_data.contents)

        access_data = access_table.to_domain()

        self.assertEqual(access_table.id, access_data.item_id)
        self.assertEqual(access_table.title, access_data.title)
        self.assertEqual(access_table.contents, access_data.contents)

    def test_create(self):
        access_data = _make_sample_data(2)

        result: MyDomain = self.repository.create(access_data)

        # assert len(self.samples) == 11
        self.assertIsInstance(result, MyDomain)
        self.assertEqual(result.item_id, 2)
        self.assertEqual(result.title, access_data.title)
        self.assertEqual(result.contents, access_data.contents)

    def test_get_item_list(self):
        access_data = _make_sample_data(1)

        result = self.repository.get_item_list()

        self.assertEqual(len(result), 1)
        result_item: MyDomain = result[0]
        self.assertIsInstance(result_item, MyDomain)
        self.assertEqual(result_item.item_id, access_data.item_id)
        self.assertEqual(result_item.title, access_data.title)
        self.assertEqual(result_item.contents, access_data.contents)


if __name__ == "__main__":
    # for vanilla unittest
    # unittest.main()
    # for all tests with pytest
    pytest.main(["-s", "-v", __file__])
    # for a specific pytest function
    # pytest.main(["-s", "-v", __file__ + "::test_specific"])
