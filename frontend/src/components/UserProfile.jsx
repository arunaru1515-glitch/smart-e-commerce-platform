import React from "react";
import "./UserProfile.css";

function UserProfile({ user, backendUser }) {
  const name =
    user?.name ||
    backendUser?.name ||
    "Not available";

  const email =
    user?.email ||
    backendUser?.email ||
    "Not available";

  const auth0Id =
    user?.sub ||
    "Not applicable for email/password login";

  return (
    <div className="profile">

      <div className="profile-header">
        <div className="profile-avatar">
          {name.charAt(0).toUpperCase()}
        </div>

        <div>
          <h2>Welcome!</h2>
          <p>Your account information</p>
        </div>
      </div>

      {user?.picture && (
        <img
          src={user.picture}
          alt="Profile"
          className="profile-image"
        />
      )}

      <div className="profile-details">

        <div className="profile-detail">
          <span>Name</span>
          <strong>{name}</strong>
        </div>

        <div className="profile-detail">
          <span>Email</span>
          <strong>{email}</strong>
        </div>

        <div className="profile-detail">
          <span>Auth0 ID</span>
          <strong className="profile-id">
            {auth0Id}
          </strong>
        </div>

      </div>

    </div>
  );
}

export default UserProfile;