import { useEffect, useState } from "react";
import "./NotificationBell.css";

const API_URL = "http://127.0.0.1:8000";

function NotificationBell({ userId, token }) {
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  // =========================================================
  // FETCH NOTIFICATIONS
  // =========================================================

  const fetchNotifications = async () => {
    if (!token) return;

    try {
      setLoading(true);

      const response = await fetch(
        `${API_URL}/notifications/`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error(
          "Failed to fetch notifications"
        );
      }

      const data = await response.json();

      console.log(
        "Notifications Response:",
        data
      );

      // Backend returns:
      // {
      //   message: "...",
      //   notifications: [...]
      // }

      setNotifications(
        Array.isArray(data.notifications)
          ? data.notifications
          : []
      );

    } catch (error) {
      console.error(
        "Notification fetch error:",
        error
      );

      setNotifications([]);

    } finally {
      setLoading(false);
    }
  };


  // =========================================================
  // MARK NOTIFICATION AS READ
  // =========================================================

  const markAsRead = async (
    notificationId
  ) => {
    if (!token) return;

    try {

      const response = await fetch(
        `${API_URL}/notifications/read?notification_id=${notificationId}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );


      if (!response.ok) {
        throw new Error(
          "Failed to mark notification as read"
        );
      }


      // Update UI immediately

      setNotifications(
        (previous) =>
          previous.map(
            (notification) =>
              notification.id ===
              notificationId
                ? {
                    ...notification,
                    read_status: "read",
                  }
                : notification
          )
      );


    } catch (error) {

      console.error(
        "Mark notification read error:",
        error
      );

    }
  };


  // =========================================================
  // INITIAL FETCH
  // =========================================================

  useEffect(() => {

    if (token) {
      fetchNotifications();
    }

  }, [token]);


  // =========================================================
  // WEBSOCKET - REAL TIME NOTIFICATIONS
  // =========================================================

  useEffect(() => {

    if (!userId || !token) {
      return;
    }


    const websocket =
      new WebSocket(
        `ws://127.0.0.1:8000/ws/${userId}`
      );


    websocket.onopen = () => {

      console.log(
        "Notification WebSocket connected"
      );

    };


    websocket.onmessage = (
      event
    ) => {

      try {

        const data =
          JSON.parse(event.data);


        console.log(
          "Real-time notification:",
          data
        );


        // Refresh notifications
        // from database

        fetchNotifications();


      } catch (error) {

        console.error(
          "WebSocket notification error:",
          error
        );

      }

    };


    websocket.onerror = (
      error
    ) => {

      console.error(
        "Notification WebSocket error:",
        error
      );

    };


    websocket.onclose = () => {

      console.log(
        "Notification WebSocket disconnected"
      );

    };


    return () => {

      websocket.close();

    };

  }, [userId, token]);


  // =========================================================
  // UNREAD COUNT
  // =========================================================

  const unreadCount =
    notifications.filter(
      (notification) =>
        notification.read_status ===
        "unread"
    ).length;


  // =========================================================
  // TOGGLE NOTIFICATION PANEL
  // =========================================================

  const toggleNotifications = () => {

    setIsOpen(
      (previous) => !previous
    );

  };


  // =========================================================
  // FORMAT DATE
  // =========================================================

  const formatDate = (
    dateValue
  ) => {

    if (!dateValue) {
      return "";
    }


    try {

      return new Date(
        dateValue
      ).toLocaleString();

    } catch {

      return "";

    }

  };


  // =========================================================
  // UI
  // =========================================================

  return (

    <div
      style={{
        position: "relative",
        display: "inline-block",
      }}
    >

      {/* =====================================================
          NOTIFICATION BELL
      ===================================================== */}

      <button
        type="button"
        onClick={toggleNotifications}
        style={{
          position: "relative",
          border: "none",
          background: "transparent",
          cursor: "pointer",
          fontSize: "24px",
          padding: "8px",
        }}
        title="Notifications"
      >

        🔔


        {/* ===================================================
            UNREAD BADGE
        =================================================== */}

        {unreadCount > 0 && (

          <span
            style={{
              position: "absolute",
              top: "0px",
              right: "0px",
              minWidth: "18px",
              height: "18px",
              padding: "0 4px",
              borderRadius: "50%",
              background: "#ef4444",
              color: "white",
              fontSize: "11px",
              fontWeight: "bold",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >

            {unreadCount > 99
              ? "99+"
              : unreadCount}

          </span>

        )}

      </button>


      {/* =====================================================
          NOTIFICATION PANEL
      ===================================================== */}

      {isOpen && (

        <div
          style={{
            position: "absolute",
            right: "0",
            top: "50px",
            width: "360px",
            maxHeight: "480px",
            overflowY: "auto",
            background: "white",
            border: "1px solid #e5e7eb",
            borderRadius: "12px",
            boxShadow:
              "0 10px 30px rgba(0,0,0,0.15)",
            zIndex: 1000,
          }}
        >

          {/* =================================================
              PANEL HEADER
          ================================================= */}

          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent:
                "space-between",
              padding: "16px",
              borderBottom:
                "1px solid #e5e7eb",
            }}
          >

            <div>

              <h3
                style={{
                  margin: 0,
                  fontSize: "18px",
                  color: "#111827",
                }}
              >
                Notifications
              </h3>


              <small
                style={{
                  color: "#6b7280",
                }}
              >

                {unreadCount > 0
                  ? `${unreadCount} unread`
                  : "No unread notifications"}

              </small>

            </div>


            {/* Refresh */}

            <button
              type="button"
              onClick={
                fetchNotifications
              }
              disabled={loading}
              style={{
                border: "none",
                background: "#f3f4f6",
                borderRadius: "8px",
                padding: "7px 10px",
                cursor: "pointer",
              }}
              title="Refresh"
            >
              ↻
            </button>

          </div>


          {/* =================================================
              NOTIFICATION LIST
          ================================================= */}

          {loading ? (

            <div
              style={{
                padding: "30px",
                textAlign: "center",
                color: "#6b7280",
              }}
            >
              Loading notifications...
            </div>

          ) : notifications.length === 0 ? (

            <div
              style={{
                padding: "35px 20px",
                textAlign: "center",
                color: "#6b7280",
              }}
            >

              <div
                style={{
                  fontSize: "32px",
                  marginBottom: "10px",
                }}
              >
                🔕
              </div>

              <div>
                No notifications yet
              </div>

            </div>

          ) : (

            notifications.map(
              (notification) => {

                const isUnread =
                  notification.read_status ===
                  "unread";


                return (

                  <div
                    key={notification.id}
                    onClick={() => {

                      if (isUnread) {

                        markAsRead(
                          notification.id
                        );

                      }

                    }}
                    style={{
                      padding:
                        "15px 16px",
                      borderBottom:
                        "1px solid #f1f5f9",
                      background:
                        isUnread
                          ? "#f0fdf4"
                          : "white",
                      cursor:
                        isUnread
                          ? "pointer"
                          : "default",
                      transition:
                        "background 0.2s",
                    }}
                  >

                    <div
                      style={{
                        display: "flex",
                        gap: "10px",
                      }}
                    >

                      {/* Status Dot */}

                      <div
                        style={{
                          width: "9px",
                          height: "9px",
                          marginTop: "6px",
                          borderRadius: "50%",
                          background:
                            isUnread
                              ? "#22c55e"
                              : "#d1d5db",
                          flexShrink: 0,
                        }}
                      />


                      {/* Content */}

                      <div
                        style={{
                          flex: 1,
                        }}
                      >

                        <div
                          style={{
                            fontSize: "14px",
                            fontWeight:
                              isUnread
                                ? "600"
                                : "500",
                            color: "#111827",
                            lineHeight:
                              "1.5",
                          }}
                        >
                          {notification.message}
                        </div>


                        {/* Timestamp */}

                        <div
                          style={{
                            marginTop: "5px",
                            fontSize: "12px",
                            color: "#9ca3af",
                          }}
                        >

                          {formatDate(
                            notification.timestamp
                          )}

                        </div>


                        {/* Unread message */}

                        {isUnread && (

                          <div
                            style={{
                              marginTop: "6px",
                              fontSize: "11px",
                              color: "#16a34a",
                            }}
                          >
                            Click to mark as read
                          </div>

                        )}

                      </div>

                    </div>

                  </div>

                );

              }
            )

          )}

        </div>

      )}

    </div>

  );
}


// =========================================================
// EXPORT
// =========================================================

export default NotificationBell;