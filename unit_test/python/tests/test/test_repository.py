import unittest
import pytest
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import Sequence
from sqlalchemy import Table
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeMeta
from sqlalchemy.orm import Session

# primary_key + autoincrement 필드를 교체하여 clone table을 생성한다.
def _make_cloned_table(table_type: Table | type[DeclarativeMeta], pk_fields: list[str] | None = None) -> Table:
    if isinstance(table_type, Table):
       table = table_type
    elif issubclass(type(table_type), DeclarativeMeta):
       table = table_type.__table__
    else:
       return None
    cols: list[Column] = []
    for col in table.columns:
        if (pk_fields and col.name in pk_fields) or (table.autoincrement_column == col and type(col.default) is not Sequence):
            col.default = Sequence(f"{table.name}_{col.name}_seq")
            # col.server_default = text(f"nextval('{table.name}_{col.name}_seq')")
        cols.append(col._copy())
    cloned_table = Table(
        table.name,
        MetaData(),  # 새로운 메타데이터로 충돌 방지
        *cols
    )
    return cloned_table

def _make_sample_data(item_id: int = 1) -> MyDomain:
    sample_data = MyDomain(
        item_id=item_id,
        title=f"Sample {item_id}",
    )
    return sample_data

class TestMyDatabaseRepository(unittest.TestCase):
    def __init__(self, methodName="runTest"):
        super().__init__(methodName)
        self.repository = MyRepository()

    def get_sample_data(self, item_id: int = 1):
        return _make_sample_data(item_id)

    def write_records(self, max_count: int):
        session: Session = next(db.session())
        for i in range(1, max_count + 1):
            data = _make_sample_data(i, i - 1)
            session.add(MyTable.from_domain(data))
        session.commit()

    def setUp(self):
        try:
            db.init_app(
                app=None,
                # database_url="sqlite:///:memory:",
                database_url="duckdb:///:memory:",
                connect_args={
                    # "check_same_thread": False,
                },
            )
            # db.create_table()
            # db.create_table(tables=[Base.metadata.tables["access_control"]])
            # MyTable.__table__.create(bind=db.engine)

            cloned_table = _make_cloned_table(MyTable)
            cloned_table.create(bind=db.engine)
            self.write_records(10)
        except Exception as e:
            print(e)

    def tearDown(self):
        db.shutdown()
        return super().tearDown()

    def test_get_item_list(self):
        access_data = self.get_sample_data(10)

        result = self.repository.get_item_list()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 10)
        result_item: MyDomain = result[0]
        self.assertIsInstance(result_item, MyDomain)
        self.assertEqual(result_item.item_id, access_data.item_id)
        self.assertEqual(result_item.title, access_data.title)

if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])
