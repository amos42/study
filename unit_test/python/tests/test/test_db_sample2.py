import unittest
from functools import wraps
from typing import Type
from typing import TypeVar
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

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
        self.engine = create_engine("sqlite:///:memory:")
        self.session = sessionmaker(autoflush=False, bind=self.engine)

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

def _make_mock_session(self):
    mock_session = Mock()

    def get_side_effect(tbl, pk):
        return next((s for s in self.samples if s.id == pk), None)

    mock_session.get.side_effect = Mock(side_effect=get_side_effect)

    def add_side_effect(tbl):
        self.samples.append(tbl)
        self.current_session_record = tbl

    mock_session.add = Mock(side_effect=add_side_effect)
    mock_session.commit = Mock()

    def delete_side_effect(tbl):
        self.samples.remove(tbl)

    mock_session.delete = Mock(side_effect=delete_side_effect)
    mock_session.flush = Mock()

    def refresh_side_effect(tbl):
        tbl.__dict__.update(self.current_session_record.__dict__)

    mock_session.refresh = Mock(side_effect=refresh_side_effect)

    def scalars_side_effect(*args, **kwargs):
        scalar = MagicMock()

        def all_side_effect() -> list[MyTable]:
            self.samples.sort(key=lambda x: x.created_at, reverse=True)
            return self.samples

        scalar.all = Mock(side_effect=all_side_effect)

        def first_side_effect() -> MyTable | None:
            if not self.samples or len(self.samples) == 0:
                return None
            self.samples.sort(key=lambda x: x.created_at, reverse=True)
            return self.samples[0]

        scalar.first = Mock(side_effect=first_side_effect)

        def one_side_effect() -> MyTable:
            if not self.samples or len(self.samples) == 0:
                raise Exception("No result found")
            self.samples.sort(key=lambda x: x.created_at, reverse=True)
            return self.samples[0]

        scalar.one = Mock(side_effect=one_side_effect)
        return scalar

    mock_session.scalars = Mock(side_effect=scalars_side_effect)

    def query_side_effect(*args, **kwargs):
        query = MagicMock()
        query._filtered.return_value = self.samples
        query._offset.return_value = None
        query._limit.return_value = None

        def offset_side_effect(offset_value: int):
            query._offset.return_value = offset_value
            return query

        def limit_side_effect(limit_value: int):
            query._limit.return_value = limit_value
            return query

        def filter_side_effect(*args, **kwargs):
            filtered = query._filtered.return_value
            for condition in args:
                if hasattr(condition.left, "name") and condition.left.name == "id":
                    value = condition.right.value
                    filtered = [s for s in filtered if s.id == value]
                if hasattr(condition.left, "name") and condition.left.name == "title":
                    value = condition.right.value
                    filtered = [s for s in filtered if s.title == value]
                if hasattr(condition.left, "name") and condition.left.name == "contents":
                    value = condition.right.value
                    filtered = [s for s in filtered if s.contents == value]
            query._filtered.return_value = filtered
            return query

        def order_by_side_effect(*args, **kwargs):
            # lst = query._filtered()
            # lst.sort(key=lambda x: x.created_at, reverse=True)
            # query._filtered.return_value = lst
            return query

        def first_side_effect() -> MyTable | None:
            lst = query._filtered()
            if not lst:
                return None
            if len(lst) == 0:
                return None
            return lst[0]

        def all_side_effect() -> list[MyTable]:
            offset = query._offset()
            limit = query._limit()
            if not offset or not limit:
                return query._filtered()
            lst = query._filtered()
            return lst[offset : offset + limit]

        def count_side_effect() -> int:
            cnt = len(query._filtered())
            offset = query._offset()
            limit = query._limit()
            if not offset or not limit:
                return cnt
            cnt -= offset
            if cnt < 0:
                return 0
            return min(cnt, limit)

        query.filter = Mock(side_effect=filter_side_effect)
        query.offset = Mock(side_effect=offset_side_effect)
        query.limit = Mock(side_effect=limit_side_effect)
        query.order_by = Mock(side_effect=order_by_side_effect)
        query.first = Mock(side_effect=first_side_effect)
        query.all = Mock(side_effect=all_side_effect)
        query.count = Mock(side_effect=count_side_effect)
        return query

    mock_session.query = Mock(side_effect=query_side_effect)

    return mock_session

class TestDatabaseMyRepository(unittest.TestCase):
    samples: list[MyTable]
    current_session_record: MyTable = None

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.repository = MyRepository()

    def create_db_mock(self):
        db_mock = Mock()
        db_mock.engine = Mock()
        db_mock.engine.pool = Mock()
        db_mock.engine.pool.status = Mock(return_value="active")
        db_mock.session = Mock(side_effect=lambda: iter([self.mock_session]))
        return db_mock

    def setUp(self):
        self.samples = _make_sample_table_data_list(10)
        self.mock_session = _make_mock_session(self)

        db_mock = self.create_db_mock()
        self.db_patch = patch("test_db_sample.db", db_mock)
        self.db_patch.start()

    def tearDown(self):
        self.db_patch.stop()

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
        access_data = _make_sample_data()

        result: MyDomain = self.repository.create(access_data)

        assert len(self.samples) == 11
        self.assertIsInstance(result, MyDomain)
        self.assertEqual(result.item_id, 1)
        self.assertEqual(result.title, access_data.title)
        self.assertEqual(result.contents, access_data.contents)

    def test_get_item_list(self):
        access_data = _make_sample_data(1)

        result = self.repository.get_item_list()

        self.assertEqual(len(result), 10)
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
