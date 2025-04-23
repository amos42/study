## 초기화

```bash
$ npm install
```

## 빌드

```bash
$ npm run build
```

## 실행

```bash
$ npm run start
```

## 배포

```bash
$ docker-compose up -d
```

## DB 초기화

* 윈도우의 경우
```bash
> type initdb.sql | docker exec -i log-db psql -U log-getter -d log_db
```

* 리눅스의 경우
```bash
$ cat initdb.sql | docker exec -i log-db psql -U log-getter -d log_db
```

## 재배포

```bash
$ docker-compose down
$ docker rmi log-getter
$ docker-compose up -d
```
