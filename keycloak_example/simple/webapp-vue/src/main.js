import { createApp } from 'vue'
import App from './App.vue'
// import router from './router'; // 만약 라우터를 사용 중이라면
import Keycloak from 'keycloak-js';

const initOptions = {
  url: 'http://localhost:8080/',
  realm: 'master',
  clientId: 'test2'
};

const keycloak = new Keycloak(initOptions);

keycloak.init({ onLoad: 'login-required' })
  .then(authenticated => {
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
