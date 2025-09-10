# Keycloak 유저 관리

랠름의 속성에 유저를 위한 프로퍼티를 추가한다.




## Client

프론트엔드용과 백엔드용 client가 각각 한개씩 필요하다.

![](images/keycloak_01.png)

### frontend clinet

이름: test-fe

* Always display in UI : True
* Root URL
* Valid redirect URIs
* Web origins
* Client authentication : False
* Authentication flow 
  * Standard flow : True
  * Direct access grants : False


client를 생성해서 authorization은 켜면 안 된다.

만약 토큰에 테넌트 정보를 포함하고 싶다면 다음과 같이 한다.



### backend client

이름: test-be

백엔드용 client를 생성해서 authorization을 추가하여 secret을 생성한다.

service-roles 옵션을 켜면 자동으로 service account가 하나 생성되는데, 이름은 service-account-<client이름> 라는 이름으로 생성된다.

> test-be -> service-account-test-be

이 account에 추가적으로 다음의 role을 더 부여한다.


* \<realm>/view-clients
* \<realm>/manage-users
* \<realm>/view-users
* \<realm>/view-events




## 구현

**필요한 파라미터들**


.env

```ini
KEYCLOAK_SERVER_URL = "http://localhost:8080" // 서버 주소
KEYCLOAK_REALM_NAME = master                  // 랠름 이름
KEYCLOAK_CLIENT_ID = test-be                  // Grant 접근 가능한 백엔드 클라이언트
KEYCLOAK_CLIENT_SECRET = "........."          // 백엔드 클라이언트 시크릿
KEYCLOAK_CLIENT_UUID = "......."              // 백엔드 클라이언트 ID
KEYCLOAK_ADMIN_USER = test-be-service-account // admin ID
KEYCLOAK_FRONTEND_CLIENT_ID = test-fe         // 프론트엔드 로그인 담당 클라이언트 (세션 정보 얻기 위함)
```


**Keycloak 개체 생성**

```python
KEYCLOAK_SERVER_URL = os.getenv("KEYCLOAK_SERVER_URL")
KEYCLOAK_REALM_NAME = os.getenv("KEYCLOAK_REALM_NAME")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID")
KEYCLOAK_CLIENT_UUID = os.getenv("KEYCLOAK_CLIENT_UUID")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET")
KEYCLOAK_ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER")
KEYCLOAK_FRONTEND_CLIENT_ID = os.getenv("KEYCLOAK_FRONTEND_CLIENT_ID")

keycloak_admin = KeycloakAdmin(
    server_url = KEYCLOAK_SERVER_URL,
    username = KEYCLOAK_ADMIN_USER,
    realm_name = KEYCLOAK_REALM_NAME,
    client_id = KEYCLOAK_CLIENT_ID,
    client_secret_key = KEYCLOAK_CLIENT_SECRET,
    verify=True
)
```

**전체 유저 수**


```python
total_users = keycloak_admin.users_count({})
```

**현재 접속 한 유저 수**


```python
sessions = keycloak_admin.get_client_all_sessions(client_id=KEYCLOAK_CLIENT_UUID)
active_user_ids = set(session['userId'] for session in sessions)
active_users = len(active_user_ids)
```

**특정 유저 정보**


```python
user = keycloak_admin.get_user(user_id)
```

**전체 유저 목록**


```python
users = keycloak_admin.get_users({"first": start, "max": page_size})
```

**특정 유저 접속 이력**


```python
events = keycloak_admin.get_events({"user":user_id, "client":KEYCLOAK_FRONTEND_CLIENT_ID, "type":["LOGIN","LOGOUT","LOGIN_ERROR"], "direction":"desc", "first": start, "max": page_size})
```



## Frontent 앱


```javascript
const keycloak = new Keycloak({
  url: 'http://localhost:8080/',
  realm: 'master',
  clientId: 'test-fe',
});
```

**React의 경우**

```javascript
const root = ReactDOM.createRoot(document.getElementById('root'));

keycloak.init({ onLoad: 'login-required' }).then((authenticated) => {
  if (authenticated) {
    root.render(
      <React.StrictMode>
        <App />
      </React.StrictMode>
    );
  }
});
```

**Vue3의 경우**

```javascript
keycloak.init({ onLoad: 'login-required' }).then(authenticated => {
    if (!authenticated) {
      window.location.reload();
    } else {
      const app = createApp(App);
      app.config.globalProperties.$keycloak = keycloak; // 전역으로 keycloak 객체를 노출
    //   app.use(router); // 라우터 사용
      app.mount('#app');
    }
  })
  .catch(() => {
    console.error('인증 초기화 실패');
  });
```


pytest를 위해서는 디상 디렉토리를 등록해 준다.

```
set PYTHONPATH=%cd%
```