const express = require('express');
const session = require('express-session');
const Keycloak = require('keycloak-connect');
const axios = require('axios');

const memoryStore = new session.MemoryStore();

const app = express();

app.use(session({
    secret: 'some super secret',
    resave: false,
    saveUninitialized: true,
    store: memoryStore
}));

// cors 설정
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    if (req.method === 'OPTIONS') {
        return res.sendStatus(204);
    }
    next();
});

let keycloak;

const kcConfig = {
    "realm": "master",
    "auth-server-url": "http://localhost:8080/",
    "ssl-required": "external",
    "resource": "test",
    // "credentials": {
    //     "secret": "8QwyK9v2Mt5oVd7wQSjOywqmKZUOCUHg"
    // },
    "confidential-port": 0
};

keycloak = new Keycloak({store: memoryStore}, kcConfig);
app.use(keycloak.middleware());

app.get('/api/v1/apps', keycloak.protect(), async (req, res) => {
    console.log(req.kauth.grant.access_token.token)
    try {
        const response = await axios.get('http://localhost:8080/realms/master/account/applications', {
            headers: {
                Authorization: `Bearer ${req.kauth.grant.access_token.token}`
            }
        });
        res.json(response.data);
    } catch (error) {
        res.status(error.response.status).json(error.response.data);
    }
});

app.get('/', keycloak.protect(), (req, res) => {
    res.sendFile(__dirname + '/public/index.html');
});

// /js 디렉토리 아래의 파일 요청시, 해당 위치의 파일 읽어서 리턴
app.get('/js/:filename', (req, res) => {
    res.sendFile(__dirname + `/public/js/${req.params.filename}`);
    console.log(`Sending file: /public/js/${req.params.filename}`);
    res.on('finish', () => {
        console.log(`File sent: /public/js/${req.params.filename}`);
        console.log(`Status code: ${res.statusCode}`);
    });
});

app.listen(3000, () => {
    console.log('Server is running on http://localhost:3000');
});
