<template>
  <div>
    <h2>User Info</h2>
    <ul>
      <li>{{ message }}</li>
      <li>{{ message2 }}</li>
      <li>{{ message3 }}</li>
      <li>{{ message4 }}</li>
    </ul>
    <button @click="logout">로그아웃</button>
  </div>
</template>

<script>
export default {
  data() {
    return {
      message: '',
      message2: '',
      message3: '',
      message4: '',
    };
  },
  methods: {
    logout() {
      this.$keycloak.logout();
    }
  },
  mounted() {
    this.message = `User: ${this.$keycloak.tokenParsed.preferred_username}`;
    this.message2 = `Roles: ${this.$keycloak.realmAccess.roles.join(", ")}`;
    this.message3 = `Realm: ${this.$keycloak.realm}`;
    this.message4 = `Token: ${this.$keycloak.token}`;    
  }
};
</script>

