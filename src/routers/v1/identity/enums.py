"""Identity enums."""

from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    DRIVER = "driver"


class IdentityAction(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE_USER = "create_user"
    GET_PROFILE = "get_profile"
