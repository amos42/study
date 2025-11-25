from sqlalchemy import (
    Sequence,
    Table,
    create_engine,
    Column,
    Integer,
    String,
    MetaData,
    # text,
)
from sqlalchemy.orm import declarative_base, DeclarativeMeta
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable


Base = declarative_base()


class MyTestTable(Base):
    __tablename__ = "test"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True) # postgresql의 경우엔 SERIAL 타입으로 생성됨
    # id = Column(Integer, Sequence('test_id_seq'), primary_key=True, index=True, autoincrement=True)
    title = Column(String)
    contents = Column(String)
    # tags = Column(ARRAY(String))


# 데이터베이스 엔진을 생성한다.
# engine = create_engine('postgresql://test:password@localhost:5432/test_db')
# engine = create_engine('sqlite:///:memory:')
engine = create_engine("duckdb:///:memory:")

# 테이블을 생성한다.
# Base.metadata.create_all(engine)

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

cloned_table = _make_cloned_table(MyTestTable)
# cloned_table = _make_cloned_table(MyTestTable.__table__)

# table = MyTestTable.__table__
table = cloned_table
print(CreateTable(table))

table.drop(bind=engine, checkfirst=True)
table.create(bind=engine)

# 세션을 생성한다.
with Session(engine) as session:
    # 데이터를 삽입한다.
    data = MyTestTable(title="테스트#1", contents="테스트 데이터 1")
    session.add(data)
    data = MyTestTable(title="테스트#2", contents="테스트 데이터 2")
    session.add(data)
    session.commit()

    # 데이터를 조회한다.
    datas = session.query(MyTestTable).all()
    for data in datas:
        print(f'{data.id}: {data.title} "{data.contents}"')
