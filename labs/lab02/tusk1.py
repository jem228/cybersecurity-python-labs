import hashlib
import hmac
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

PASSWORD_ITERATIONS = 600_000
SESSION_TIMEOUT_SEC = 900


class User:
    def __init__(self, username, email, role="user", active=True):
        self.username = username
        self.email = email
        self.role = role
        self.active = active
        self.__password_hash = None
        self.__password_salt = None

    @property
    def email(self):
        return self.__email

    @email.setter
    def email(self, value):
        pattern = r"^[\w.+-]+@[\w-]+(?:\.[\w-]+)+$"

        if not isinstance(value, str) or not re.fullmatch(pattern, value):
            raise ValueError("Некоректна адреса електронної пошти")

        self.__email = value

    def set_password(self, password):
        if not isinstance(password, str) or not password:
            raise ValueError("Пароль не може бути порожнім")

        self.__password_salt = os.urandom(16)
        self.__password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PASSWORD_ITERATIONS,
        )

    def check_password(self, password):
        if (
            not isinstance(password, str)
            or self.__password_hash is None
            or self.__password_salt is None
        ):
            return False

        candidate_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PASSWORD_ITERATIONS,
        )

        return hmac.compare_digest(
            self.__password_hash,
            candidate_hash,
        )


class Admin(User):
    def __init__(self, username, email, active=True):
        super().__init__(
            username,
            email,
            role="admin",
            active=active,
        )
        self.permissions = set()

    def grant_permission(self, permission):
        if not isinstance(permission, str) or not permission.strip():
            raise ValueError("Назва дозволу не може бути порожньою")

        self.permissions.add(permission)

    def revoke_permission(self, permission):
        self.permissions.discard(permission)

    def has_permission(self, permission):
        return permission in self.permissions


@dataclass
class Session:
    ip: str
    login_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not isinstance(self.ip, str) or not self.ip.strip():
            raise ValueError("IP-адреса не може бути порожньою")

        for value in (self.login_time, self.last_activity):
            if (
                not isinstance(value, datetime)
                or value.tzinfo is None
                or value.utcoffset() is None
            ):
                raise ValueError("Час сесії повинен містити часовий пояс")

    def touch(self):
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self, timeout_sec=SESSION_TIMEOUT_SEC):
        if (
            not isinstance(timeout_sec, (int, float))
            or isinstance(timeout_sec, bool)
            or timeout_sec < 0
        ):
            raise ValueError("Таймаут не може бути від'ємним")

        now = datetime.now(timezone.utc)
        elapsed = now - self.last_activity

        return elapsed < timedelta(seconds=timeout_sec)


@dataclass
class AuditEvent:
    timestamp: datetime
    username: str
    action: str
    details: str = ""

    def __post_init__(self):
        if (
            not isinstance(self.timestamp, datetime)
            or self.timestamp.tzinfo is None
            or self.timestamp.utcoffset() is None
        ):
            raise ValueError("Час події повинен містити часовий пояс")


@dataclass
class AuditLog:
    events: list[AuditEvent] = field(default_factory=list)

    def log_event(self, username, action, details=""):
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc),
            username=username,
            action=action,
            details=details,
        )
        self.events.append(event)
        return event

    def show_events(self):
        for event in self.events:
            print(
                f"[{event.timestamp.isoformat()}] "
                f"User: {event.username} | "
                f"Action: {event.action} | "
                f"Details: {event.details}"
            )


class UserAccount:
    def __init__(self, user, session=None, audit_log=None):
        if not isinstance(user, User):
            raise TypeError("user повинен бути об'єктом класу User або Admin")

        if session is not None and not isinstance(session, Session):
            raise TypeError("session повинен бути об'єктом класу Session")

        if audit_log is not None and not isinstance(audit_log, AuditLog):
            raise TypeError("audit_log повинен бути об'єктом класу AuditLog")

        self.user = user
        self.session = session
        self.audit_log = audit_log if audit_log is not None else AuditLog()

    def login(self, username, password, ip):
        if self.is_authenticated():
            self.audit_log.log_event(
                username,
                "login_failed",
                "Сесія вже активна",
            )
            return False

        if self.session is not None:
            self.session = None

        if (
            not self.user.active
            or username != self.user.username
            or not self.user.check_password(password)
        ):
            self.audit_log.log_event(
                username,
                "login_failed",
                "Невірні облікові дані або неактивний обліковий запис",
            )
            return False

        self.session = Session(ip=ip)
        self.audit_log.log_event(
            username,
            "login_success",
            f"IP: {ip}",
        )
        return True

    def is_authenticated(self):
        return (
            self.user.active and self.session is not None and self.session.is_active()
        )

    def logout(self):
        if self.session is not None:
            self.audit_log.log_event(
                self.user.username,
                "logout",
            )
            self.session = None
            return True

        return False

    def __getitem__(self, key):
        if key == "username":
            return self.user.username

        if key == "role":
            return self.user.role

        raise KeyError(key)
