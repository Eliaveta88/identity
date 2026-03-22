"""Description strings for identity endpoints."""

LOGIN_DESC = (
    "Authenticate user with username and password. "
    "Returns access and refresh JWT tokens. "
    "Action: LOGIN"
)

REFRESH_TOKEN_DESC = (
    "Exchange a valid refresh JWT for new access and refresh tokens. "
    "Previous refresh token is invalidated (rotation). "
    "Action: REFRESH"
)

LOGOUT_DESC = (
    "Logout user and revoke current session token. "
    "Invalidates the access token for security. "
    "Action: LOGOUT"
)

LOGOUT_ALL_DESC = (
    "Logout user from all active sessions. "
    "Revokes every active session associated with the account. "
    "Action: LOGOUT_ALL"
)

GET_CURRENT_USER_DESC = (
    "Get profile of currently authenticated user. "
    "Requires valid access token in Authorization header. "
    "Action: GET_PROFILE"
)

CREATE_USER_DESC = (
    "Create new user account. "
    "Username and email must be unique. "
    "Password will be hashed before storage. "
    "Action: CREATE_USER"
)
