from sqlalchemy import ARRAY, Sequence, Table, create_engine, Column, Integer, String, MetaData, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable
 
 
Base = declarative_base()
 
class MyTest(Base):
    __tablename__ = 'test'
 
    id = Column(Integer, primary_key=True, autoincrement=True)  # postgresql의 경우엔 SERIAL 타입으로 생성됨
    # id = Column(Integer, Sequence('mytest_id_seq'), primary_key=True, index=True)
    name = Column(String)
    password = Column(String)
    tags = Column(ARRAY(String))
 
 
# 데이터베이스 엔진을 생성합니다.
# engine = create_engine('postgresql://test:password@localhost:5432/test_db')
# engine = create_engine('sqlite:///:memory:')
engine = create_engine('duckdb:///:memory:')
 
# 테이블을 생성합니다.
# Base.metadata.create_all(engine)
 
cloned_table = Table(
    MyTest.__tablename__,
    MetaData(),  # 새로운 메타데이터로 충돌 방지
    *[
        # col._copy() if col.name != "id" else Column("id", Integer, Sequence('mytest_id_seq'), primary_key=True, index=True, autoincrement=True)
        col._copy() if col.name != "id" else Column("id", Integer, Sequence('mytest_id_seq'), primary_key=True, index=True, autoincrement=True, server_default=text("nextval('mytest_id_seq')"))
        for col in MyTest.__table__.columns
    ]
)
 
print(CreateTable(cloned_table))
 
table = cloned_table
# table = MyTest.__table__
table.drop(bind=engine, checkfirst=True)
# seq = Sequence('mytest_id_seq')
# seq.create(bind=engine)  # 시퀀스 먼저 생성
table.create(bind=engine)
 
 
# 세션을 생성합니다.
with Session(engine) as session:
    # # 사용자 데이터를 삽입합니다.
    user = MyTest(name="홍길동", password="password")
    session.add(user)
    user = MyTest(name="홍길동2", password="password")
    session.add(user)
    session.commit()
 
    # 사용자 데이터를 조회합니다.
    users = session.query(MyTest).all()
    for user in users:
        print(user.id, user.name, user.password)
