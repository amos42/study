from typing import Any
from alembic import op
from sqlalchemy import ARRAY, Sequence, Table, Column, Integer, String
from sqlalchemy import MetaData, create_engine, schema #, text
from sqlalchemy.orm import declarative_base, DeclarativeMeta
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateColumn
from sqlalchemy.schema import CreateTable, CreateSequence
from sqlalchemy.sql.schema import ddl
from sqlalchemy.sql.compiler import DDLCompiler
from sqlalchemy.ext.compiler import compiles
import re

Base = declarative_base()

class MyTestTable(Base):
    __tablename__ = "test"

    id = Column(Integer, primary_key=True, autoincrement=True) # postgresql의 경우엔 SERIAL 타입으로 생성됨
    # id = Column(Integer, Sequence('test_id_seq'), primary_key=True, autoincrement=True)
    title = Column(String)
    contents = Column(String)
    # tags = Column(ARRAY(String), nullable=True)


# @compiles(CreateTable, "duckdb")  # type: ignore[misc]
# def visit_create_table_with_serial_support(
#     instance: CreateTable, compiler: DDLCompiler, **kw: Any
# ) -> str:
#     """Prepend a table with an auto-incremented primary key with the necessary sequence."""
#     table_sql = compiler.visit_create_table(instance, **kw)
#     table_name = instance.element.name
#     seq_sql = f"\nCREATE SEQUENCE {'test_id_seq'};"
#     return seq_sql + table_sql

@compiles(CreateSequence, 'duckdb')
def my_sequence(element, compiler, **kw):
    return compiler.visit_create_sequence(element, **kw)

# @compiles(CreateColumn, 'duckdb')
# def my_column(element, compiler, **kw):
#     column = element.element
#     # if column.primary_key and column.autoincrement:
#     if column == column.table.autoincrement_column:
#         seq = Sequence(f"{column.table.name}_{column.name}_seq")
#         # column.default = Sequence(f"{column.table.name}_{column.name}_seq")
#         column.default = seq
#         # compiler.traverse_single(column.default)
#         # compiler.visit_create_sequence(CreateSequence(seq), create_ok=True)
#         # ddl.SchemaGenerator.traverse_single(obj=seq, create_ok=True)
#     return compiler.visit_create_column(element, **kw)

# def _serial_sequence_name(table_name: str) -> str:
#     return f"{table_name}_id_seq"

# @compiles(CreateTable, "duckdb")  # type: ignore[misc]
# def visit_create_table_with_serial_support(
#     instance: CreateTable, compiler: DDLCompiler, **kw: Any
# ) -> str:
#     """Prepend a table with an auto-incremented primary key with the necessary sequence."""
#     # return compiler.visit_create_table(instance, **kw)
#     table_sql = compiler.visit_create_table(instance, **kw)
#     table_name = instance.element.name
#     seq_name = _serial_sequence_name(table_name)
#     if seq_name not in table_sql:
#         # no need to create a sequence
#         return table_sql
#     seq_sql = f"\nCREATE SEQUENCE {seq_name};"
#     return  seq_sql + table_sql
@compiles(CreateTable, "duckdb")  # type: ignore[misc]
def visit_create_table_with_serial_support(
    instance: CreateTable, compiler: DDLCompiler, **kw: Any
) -> str:
    """Prepend a table with an auto-incremented primary key with the necessary sequence."""
    # return compiler.visit_create_table(instance, **kw)
    table_sql = compiler.visit_create_table(instance, **kw)
    pattern = r"nextval\(['\"]([^'\"]+)['\"]\)"
    seqs = re.findall(pattern, table_sql)
    if len(seqs) <= 0:
        return table_sql
    seq_sql = f"\nCREATE SEQUENCE {seqs[0]};"
    return  seq_sql + table_sql

@compiles(CreateColumn, "duckdb")  # type: ignore[misc]
def visit_create_column_with_serial_support(
    instance: CreateColumn, compiler: DDLCompiler, **kw: Any
) -> str:
    """Replace the first SERIAL field with a duckdb-style auto-incremented integer."""
    column_sql = compiler.visit_create_column(instance, **kw)
    if "SERIAL" not in column_sql or not kw.get("first_pk"):
        return column_sql
    column = instance.element
    autoinc_type = f"INTEGER DEFAULT(nextval('{column.table.name}_{column.name}_seq'))"
    return column_sql.replace("SERIAL", autoinc_type)

log_disp = True
# 데이터베이스 엔진을 생성한다.
# engine = create_engine('postgresql://test:password@localhost:5432/test_db', echo=log_disp)
# engine = create_engine('sqlite:///:memory:', echo=log_disp)
engine = create_engine("duckdb:///:memory:", echo=log_disp)

# seq_obj = Sequence('test_id_seq', metadata=Base.metadata)

# op.execute(schema.CreateSequence(seq_obj))

# primary_key + autoincrement 필드를 교체하여 clone table을 생성한다.
# def _make_cloned_table(table_type: Table | type[DeclarativeMeta], pk_fields: list[str] | None = None) -> Table:
#     if isinstance(table_type, Table):
#        table = table_type
#     elif issubclass(type(table_type), DeclarativeMeta):
#        table = table_type.__table__
#     else:
#        return None
#     cols: list[Column] = []
#     for col in table.columns:
#         if (pk_fields and col.name in pk_fields) or (table.autoincrement_column == col and type(col.default) is not Sequence):
#             col.default = Sequence(f"{table.name}_{col.name}_seq")
#             # col.server_default = text(f"nextval('{table.name}_{col.name}_seq')")
#         cols.append(col._copy())
#     cloned_table = Table(
#         table.name,
#         MetaData(),  # 새로운 메타데이터로 충돌 방지
#         *cols
#     )
#     return cloned_table

# cloned_table = _make_cloned_table(MyTestTable)
# cloned_table = _make_cloned_table(MyTestTable.__table__)

table = MyTestTable.__table__
# # table = cloned_table

# print(CreateTable(table))
# table.drop(bind=engine, checkfirst=True)
table.create(bind=engine)

# 테이블을 생성한다.
# Base.metadata.create_all(engine)
# Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables["test"]])
# Base.metadata.create_all(bind=engine, tables=[MyTestTable.__table__])
# Base.metadata.create_all(bind=engine, tables=[table])


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
    print("==========================================")
    for data in datas:
        print(f'> {data.id}: {data.title} "{data.contents}"')
    print("==========================================")

# table.drop(bind=engine, checkfirst=True)
# Base.metadata.drop_all(bind=engine)

