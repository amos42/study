import React from 'react';
import { useKeycloak } from '@react-keycloak/web';

function HomePage() {
  const { keycloak, initialized } = useKeycloak();

  if (!initialized) {
    return <div>로딩 중...</div>;
  }

  if (!keycloak.authenticated) {
    return <div>인증되지 않음 <button onClick={() => keycloak.login()}>로그인</button></div>;
  }

  return (
    <div>
      <h1>환영합니다, {keycloak.tokenParsed.preferred_username}님!</h1>
      <button onClick={() => keycloak.logout()}>로그아웃</button>
    </div>
  );
}

export default HomePage;
