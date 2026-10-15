from labs.lab02.tusk1 import (
    Admin,
    AuditLog,
    User,
    UserAccount,
)


def demo():
    """Demonstrate user accounts, permissions and audit logging."""
    print("=== Демонстрація завдання 1 ===")

    user = User("student", "student@example.com")
    user.set_password("Password123")

    print("Правильний пароль:", user.check_password("Password123"))
    print("Неправильний пароль:", user.check_password("wrong"))

    try:
        user.email = "invalid-email"
    except ValueError as error:
        print("Перевірка email:", error)

    admin = Admin("admin", "admin@example.com")
    admin.grant_permission("manage_users")
    print("Дозвіл адміністратора:", admin.has_permission("manage_users"))
    admin.revoke_permission("manage_users")
    print("Після скасування:", admin.has_permission("manage_users"))

    audit_log = AuditLog()
    account = UserAccount(user, audit_log=audit_log)

    print(
        "Вхід із неправильним паролем:",
        account.login("student", "wrong", "192.168.1.10"),
    )
    print(
        "Вхід із правильним паролем:",
        account.login("student", "Password123", "192.168.1.10"),
    )
    print("Сесія активна:", account.is_authenticated())

    print("Ім'я користувача:", account["username"])
    print("Роль:", account["role"])

    account.logout()
    print("\n=== Журнал аудиту ===")
    audit_log.show_events()


if __name__ == "__main__":
    demo()
