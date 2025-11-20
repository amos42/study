from typing import List
from sqlalchemy import ARRAY, Sequence, Table, create_engine, Column, Integer, String, MetaData
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session


Base = declarative_base()

# 사용자와 게시글 간의 관계를 설정합니다.
#@as_declarative
class MyTest(Base):
    __tablename__ = 'test'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # id = Column(Integer, Sequence('mytest_id_seq'), primary_key=True, index=True)
    name = Column(String)
    password = Column(String)
    tags = Column(ARRAY(String))


# 데이터베이스 엔진을 생성합니다.
# engine = create_engine('postgresql://test:password@localhost:5432/test_db')  # SQLite 예시
# engine = create_engine('sqlite:///:memory:')  # SQLite 예시
engine = create_engine('duckdb:///:memory:')  # SQLite 예시

# 테이블을 생성합니다.
# Base.metadata.create_all(engine)

cloned_table = Table(
    MyTest.__tablename__,
    MetaData(),  # 새로운 메타데이터로 충돌 방지
    *[
        col.copy() if col.name != "id" else Column("id", Integer, Sequence('mytest_id_seq'), primary_key=True, index=True)
        for col in MyTest.__table__.columns
    ]
)
cloned_table.create(bind=engine)


# 세션을 생성합니다.
with Session(engine) as session:
    # # 사용자 데이터를 삽입합니다.
    # user = MyTest(id=1, name="홍길동", password="password")
    user = MyTest(name="홍길동", password="password")
    session.add(user)
    session.commit()

    # 사용자 데이터를 조회합니다.
    user = session.query(MyTest).first()
    print(user.name)

