

```bash
$ docker run --name keycloak -d --restart always \
    -p 8080:8080 \
    -e KC_BOOTSTRAP_ADMIN_USERNAME=admin \
    -e KC_BOOTSTRAP_ADMIN_PASSWORD=admin \
    keycloak/keycloak start-dev
```
