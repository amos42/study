import React, { useEffect, useState } from "react";
import axios from "axios";
import { useKeycloak } from "@react-keycloak/web";

function App() {
    const [clients, setClients] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { keycloak } = useKeycloak();
    const [rols, setRols] = useState([]);
    const [profile, setProfile] = useState({});

    useEffect(() => {
        const fetchClients = async () => {
            try {
                const response = await axios.get("http://localhost:8000/apps", {
                    headers: {
                        Authorization: `Bearer ${keycloak.token}`,
                    },
                });
                setClients(response.data);
            } catch (error) {
                setError(error);
            } finally {
                setLoading(false);
            }
        };
        const fetchProfile = async () => {
            try {
                console.log(keycloak)
                const response = await axios.get(`http://localhost:8000/users/${keycloak.subject}`, {
                    headers: {
                        Authorization: `Bearer ${keycloak.token}`,
                    },
                });
                setProfile(response.data);
            } catch (error) {
                setError(error);
            } finally {
                setLoading(false);
            }
        };

        if (keycloak.authenticated && keycloak.token) {
            const realmRoles = keycloak.realmAccess?.roles || [];
            setRols(realmRoles);

            // console.log(keycloak);

            fetchProfile();
            fetchClients();
        } else {
            // 로그인 안된 상태 처리
        }
    }, [keycloak, keycloak.authenticated, keycloak.token, keycloak.realmAccess?.roles]);

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error.message}</div>;

    return (
        <div>
            <h2>User Info</h2>
            <ul>
                <li>
                    name:{" "}
                    {keycloak?.idTokenParsed.name ||
                        keycloak?.idTokenParsed.preferred_username}
                </li>
                <li>id: {keycloak?.subject}</li>
                <li>rols: {rols.join(", ")}</li>
                <li>realm: {keycloak?.realm}</li>
                <li>clientId: {keycloak?.clientId}</li>
                <li>company: {profile.attributes.company}</li>
                <li>department: {profile.attributes.department}</li>
                <li>token: {keycloak?.token}</li>
            </ul>
            <h2>Client List</h2>
            <ul>
                {clients.map((client) => (
                    <li key={client.clientId}>
                        {client.clientId} - {client.effectiveUrl}
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default App;