import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  Container,
  Table,
  Button,
  Modal,
  Form,
  Alert,
  Navbar,
  Nav,
} from "react-bootstrap";
import keycloak from "./keycloak";

// 백엔드 API 주소
const API_URL = "http://localhost:9000";

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
  const [active_users, setActiveUsers] = useState(0);
  // Pagination state for user list
  const [userPage, setUserPage] = useState(1);
  const USERS_PAGE_SIZE = 5;
  const [selectedUser, setSelectedUser] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editAttributes, setEditAttributes] = useState({});
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // 로그인 이력 관련 상태
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [loginHistory, setLoginHistory] = useState([]);
  const [loginHistoryIndex, setLoginHistoryIndex] = useState(1);
  const [historyUser, setHistoryUser] = useState(null);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  // Pagination state for login history
  const HISTORY_PAGE_SIZE = 20;

  // 로그인 이력 불러오기 (페이지네이션 적용)
  const fetchLoginHistory = async (userId, start = 1) => {
    setIsHistoryLoading(true);
    try {
      const response = await axiosInstance.get(
        `/api/users/${userId}/login-history`,
        {
          params: { start, page_size: HISTORY_PAGE_SIZE + 1 }, // 바운더리 체크를 위해 1개를 더 읽는다.
        }
      );
      let fetchedHistory = response.data.history || [];
      setHasMore(fetchedHistory.length > HISTORY_PAGE_SIZE);
      setLoginHistory(fetchedHistory.slice(0, HISTORY_PAGE_SIZE));
      setLoginHistoryIndex(start || 1);
    } catch (err) {
      setLoginHistory([]);
      setError("로그인 이력을 불러오는 데 실패했습니다.");
    } finally {
      setIsHistoryLoading(false);
    }
  };

  // 사용자 목록을 불러오는 함수 (페이지네이션 적용)
  const fetchUsers = async (page = 1) => {
    try {
      const response = await axiosInstance.get("/api/users", {
        params: { page, page_size: USERS_PAGE_SIZE },
      });
      setUsers(response.data.users);
      setActiveUsers(response.data.active_users);
      setUserPage(response.data.page || 1);
      setTotalUsers(response.data.total_users || 0);
    } catch (err) {
      setError("사용자 목록을 불러오는 데 실패했습니다.");
      console.error(err);
    }
  };

  // 전체 유저 수, 전체 이력 수 상태 추가
  const [totalUsers, setTotalUsers] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  // 컴포넌트가 마운트될 때 사용자 목록을 불러옵니다.
  useEffect(() => {
    fetchUsers();
  }, []);

  // 유저 페이지 변경 핸들러
  const handleUserPageChange = (newPage) => {
    fetchUsers(newPage);
  };

  // 로그인 이력 페이지 변경 핸들러
  const handleHistoryPageChange = (newIndex) => {
    if (historyUser) {
      fetchLoginHistory(historyUser.id, Math.max(newIndex, 0));
    }
  };

  // 수정 버튼 클릭 핸들러
  const handleEditClick = (user) => {
    setSelectedUser(user);
    // 기존 속성이 없으면 빈 객체로 시작
    setEditAttributes(user.attributes ? { ...user.attributes } : {});
    setShowModal(true);
    setError("");
    setSuccess("");
  };

  // 모달 닫기 핸들러
  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedUser(null);
  };

  // 속성 변경 핸들러
  const handleAttributeChange = (key, value) => {
    if (key === "enabled") {
      setEditAttributes((prev) => ({ ...prev, [key]: !prev[key] }));
    } else {
      setEditAttributes((prev) => ({ ...prev, [key]: value }));
    }
  };

  // 속성 저장 핸들러
  const handleSaveChanges = async () => {
    if (!selectedUser) return;

    try {
      await axiosInstance.put(`/api/users/${selectedUser.id}`, {
        email: editAttributes.email,
        attributes: editAttributes,
      });
      setSuccess("사용자 속성이 성공적으로 저장되었습니다.");
      handleCloseModal();
      fetchUsers(); // 목록 새로고침
    } catch (err) {
      setError("속성 저장에 실패했습니다.");
      console.error(err);
    }
  };

  const handleLogout = () => {
    keycloak.logout();
  };

  // 로그인 이력 버튼 클릭 핸들러
  const handleHistoryClick = (user) => {
    setHistoryUser(user);
    setShowHistoryModal(true);
    setLoginHistory([]);
    setIsHistoryLoading(true);
    fetchLoginHistory(user.id, 1);
  };

  return (
    <>
      <Navbar bg="dark" variant="dark" expand="lg">
        <Container>
          <Navbar.Brand href="#">Keycloak User Management</Navbar.Brand>
          <Navbar.Toggle />
          <Navbar.Collapse className="justify-content-end">
            <Nav>
              <Nav.Link>
                Welcome, {keycloak.tokenParsed?.preferred_username}
              </Nav.Link>
              <Button variant="outline-light" onClick={handleLogout}>
                Logout
              </Button>
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>

      <Container className="mt-5">
        <h1>Keycloak 사용자 관리</h1>
        <div className="mb-3">
          <strong>전체 유저 수:</strong> {users.length} &nbsp;|&nbsp;
          <strong>접속 중인 유저 수:</strong> {active_users}
        </div>
        {error && <Alert variant="danger">{error}</Alert>}
        {success && <Alert variant="success">{success}</Alert>}

        <Table bordered hover>
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Email</th>
              <th>기타</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr
                key={user.id}
                className={user.enabled === false ? "disabled-row" : ""}
              >
                <td>{user.id}</td>
                <td
                  style={{ color: user.enabled === false ? "red" : "inherit" }}
                >
                  {user.username}
                  {user.enabled === false ? " (disabled)" : ""}
                </td>
                <td>{user.email}</td>
                <td>
                  <Button size="sm" onClick={() => handleEditClick(user)}>
                    속성
                  </Button>
                  &nbsp;
                  <Button size="sm" onClick={() => handleHistoryClick(user)}>
                    접속이력
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>

        {/* 유저 목록 페이지네이션 */}
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: "8px",
            marginBottom: "20px",
          }}
        >
          <Button
            variant="outline-secondary"
            size="sm"
            disabled={userPage === 1}
            onClick={() => handleUserPageChange(userPage - 1)}
          >
            이전
          </Button>
          <span>
            {userPage} / {Math.ceil(totalUsers / USERS_PAGE_SIZE)}
          </span>
          <Button
            variant="outline-secondary"
            size="sm"
            disabled={userPage >= Math.ceil(totalUsers / USERS_PAGE_SIZE)}
            onClick={() => handleUserPageChange(userPage + 1)}
          >
            다음
          </Button>
        </div>

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
                  onChange={(e) =>
                    handleAttributeChange("email", e.target.value)
                  }
                />
              </Form.Group>
              <Form.Group key="company" className="mb-3">
                <Form.Label>Company</Form.Label>
                <Form.Control
                  type="text"
                  value={editAttributes.company}
                  onChange={(e) =>
                    handleAttributeChange("company", e.target.value)
                  }
                />
              </Form.Group>
              <Form.Group key="department" className="mb-3">
                <Form.Label>Department</Form.Label>
                <Form.Control
                  type="text"
                  value={editAttributes.department}
                  onChange={(e) =>
                    handleAttributeChange("department", e.target.value)
                  }
                />
              </Form.Group>
              <Form.Group key="enabled" className="mb-3">
                <Form.Check
                  type="checkbox"
                  label="Enabled"
                  checked={selectedUser?.enabled}
                  onChange={(e) =>
                    handleAttributeChange("enabled", e.target.checked)
                  }
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
        {/* 로그인 이력 모달 */}
        <Modal
          show={showHistoryModal}
          onHide={() => setShowHistoryModal(false)}
        >
          <Modal.Header closeButton>
            <Modal.Title>{historyUser?.username}님의 접속 이력</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            {isHistoryLoading ? (
              <div>로드중...</div>
            ) : loginHistory.length === 0 ? (
              <div>이력이 없습니다.</div>
            ) : (
              <>
                <ul>
                  {loginHistory.map((item, idx) => (
                    <li key={idx + loginHistoryIndex}>
                      {item.time} - {item.clientId || ""} - {item.ip || ""}
                    </li>
                  ))}
                </ul>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "center",
                    gap: "8px",
                    marginTop: "10px",
                  }}
                >
                  <Button
                    variant="outline-secondary"
                    size="sm"
                    disabled={loginHistoryIndex <= 1}
                    onClick={() => handleHistoryPageChange(loginHistoryIndex - HISTORY_PAGE_SIZE)}
                  >
                    이전
                  </Button>
                  <span>
                    {loginHistoryIndex} - {loginHistoryIndex + loginHistory.length - 1}
                  </span>
                  <Button
                    variant="outline-secondary"
                    size="sm"
                    disabled={!hasMore}
                    onClick={() => handleHistoryPageChange(loginHistoryIndex + loginHistory.length)}
                  >
                    다음
                  </Button>
                </div>
              </>
            )}
          </Modal.Body>
          <Modal.Footer>
            <Button
              variant="secondary"
              onClick={() => setShowHistoryModal(false)}
            >
              닫기
            </Button>
          </Modal.Footer>
        </Modal>
      </Container>
    </>
  );
}

export default App;
