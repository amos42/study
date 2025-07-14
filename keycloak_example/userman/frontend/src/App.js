import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Container, Table, Button, Modal, Form, Alert, Navbar, Nav } from 'react-bootstrap';
import keycloak from './keycloak';

// 백엔드 API 주소
const API_URL = 'http://localhost:8000';

// 인증된 axios 인스턴스 생성
const axiosInstance = axios.create({
    baseURL: API_URL,
});

axiosInstance.interceptors.request.use((config) => {
    config.headers.Authorization = `Bearer ${keycloak.token}`;
    return config;
});

function App() {
    const [users, setUsers] = useState([]);
    const [selectedUser, setSelectedUser] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [editAttributes, setEditAttributes] = useState({});
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // 사용자 목록을 불러오는 함수
    const fetchUsers = async () => {
        try {
            const response = await axiosInstance.get('/api/users');
            setUsers(response.data);
        } catch (err) {
            setError('사용자 목록을 불러오는 데 실패했습니다.');
            console.error(err);
        }
    };

    // 컴포넌트가 마운트될 때 사용자 목록을 불러옵니다.
    useEffect(() => {
        fetchUsers();
    }, []);

    // 수정 버튼 클릭 핸들러
    const handleEditClick = (user) => {
        setSelectedUser(user);
        // 기존 속성이 없으면 빈 객체로 시작
        setEditAttributes(user.attributes ? { ...user.attributes } : {});
        setShowModal(true);
        setError('');
        setSuccess('');
    };

    // 모달 닫기 핸들러
    const handleCloseModal = () => {
        setShowModal(false);
        setSelectedUser(null);
    };

    // 속성 변경 핸들러
    const handleAttributeChange = (key, value) => {
        setEditAttributes(prev => ({ ...prev, [key]: value }));
    };
    
    // 속성 저장 핸들러
    const handleSaveChanges = async () => {
        if (!selectedUser) return;

        try {
            await axiosInstance.put(`/api/users/${selectedUser.id}`, {
                email: editAttributes.email,
                attributes: editAttributes
            });
            setSuccess('사용자 속성이 성공적으로 저장되었습니다.');
            handleCloseModal();
            fetchUsers(); // 목록 새로고침
        } catch (err) {
            setError('속성 저장에 실패했습니다.');
            console.error(err);
        }
    };

    const handleLogout = () => {
        keycloak.logout();
    };

    return (
        <>
            <Navbar bg="dark" variant="dark" expand="lg">
                <Container>
                    <Navbar.Brand href="#">Keycloak User Management</Navbar.Brand>
                    <Navbar.Toggle />
                    <Navbar.Collapse className="justify-content-end">
                        <Nav>
                            <Nav.Link>Welcome, {keycloak.tokenParsed?.preferred_username}</Nav.Link>
                            <Button variant="outline-light" onClick={handleLogout}>Logout</Button>
                        </Nav>
                    </Navbar.Collapse>
                </Container>
            </Navbar>

            <Container className="mt-5">
                <h1>Keycloak 사용자 관리</h1>
                {error && <Alert variant="danger">{error}</Alert>}
                {success && <Alert variant="success">{success}</Alert>}
                
                <Table striped bordered hover>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Username</th>
                            <th>Email</th>
                            <th>수정</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map(user => (
                            <tr key={user.id}>
                                <td>{user.id}</td>
                                <td>{user.username}</td>
                                <td>{user.email}</td>
                                <td>
                                    <Button variant="primary" onClick={() => handleEditClick(user)}>
                                        속성 편집
                                    </Button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </Table>

                {/* 사용자 속성 편집 모달 */}
                <Modal show={showModal} onHide={handleCloseModal}>
                    <Modal.Header closeButton>
                        <Modal.Title>{selectedUser?.username}님의 속성 편집</Modal.Title>
                    </Modal.Header>
                    <Modal.Body>
                        <Form>
                            {/* {Object.entries(editAttributes).map(([key, value]) => (
                                <Form.Group key={key} className="mb-3">
                                    <Form.Label>{key}</Form.Label>
                                    <Form.Control
                                        type="text"
                                        value={value}
                                        onChange={(e) => handleAttributeChange(key, e.target.value)}
                                    />
                                </Form.Group>
                            ))} */}

                            <Form.Group key="e-mail" className="mb-3">
                                <Form.Label>e-mail</Form.Label>
                                <Form.Control
                                    type="text"
                                    value={selectedUser?.email}
                                    onChange={(e) => handleAttributeChange("email", e.target.value)}
                                />
                            </Form.Group>
                            <Form.Group key="company" className="mb-3">
                                <Form.Label>Company</Form.Label>
                                <Form.Control
                                    type="text"
                                    value={editAttributes.company}
                                    onChange={(e) => handleAttributeChange("company", e.target.value)}
                                />
                            </Form.Group>
                            <Form.Group key="department" className="mb-3">
                                <Form.Label>Department</Form.Label>
                                <Form.Control
                                    type="text"
                                    value={editAttributes.department}
                                    onChange={(e) => handleAttributeChange("department", e.target.value)}
                                />
                            </Form.Group>
                        </Form>
                    </Modal.Body>
                    <Modal.Footer>
                        <Button variant="secondary" onClick={handleCloseModal}>
                            닫기
                        </Button>
                        <Button variant="primary" onClick={handleSaveChanges}>
                            저장
                        </Button>
                    </Modal.Footer>
                </Modal>
            </Container>
        </>
    );
}

export default App;