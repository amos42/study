import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import keycloak from './keycloak';
import { ReactKeycloakProvider } from '@react-keycloak/web';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <ReactKeycloakProvider
    authClient={keycloak}
    initOptions={{
      onLoad: 'login-required',  // 'check-sso'로 설정하면 자동 로그인을 하지 않음
      checkLoginIframe: false
    }}
  >
    <App />
  </ReactKeycloakProvider>,
  document.getElementById('root')
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
