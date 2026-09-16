from shared.student import (
    GROUP_NAME,
    STUDENT_NAME,
    VARIANT_NUMBER,
)

users = {
    "quantum_researcher": {
        "role": "quantum_security",
        "clearance": 4,
        "department": "Quantum Research",
        "active": True,
    },
    "post_quantum_dev": {
        "role": "pq_cryptographer",
        "clearance": 4,
        "department": "Post-Quantum",
        "active": True,
    },
    "network_security": {
        "role": "network_security",
        "clearance": 3,
        "department": "Network Security",
        "active": True,
    },
    "crypto_intern": {
        "role": "crypto_intern",
        "clearance": 1,
        "department": "Internship",
        "active": True,
    },
    "quantum_sim": {
        "role": "simulator",
        "clearance": 2,
        "department": "Simulation",
        "active": False,
    },
}


resources = [
    ("quantum_algorithms", 4),
    ("pq_implementations", 4),
    ("network_protocols", 3),
    ("learning_materials", 1),
    ("quantum_keys", 4),
    ("educational_content", 1),
    ("hybrid_systems", 3),
    ("quantum_computers", 4),
    ("crypto_libraries", 2),
    ("tutorials", 1),
]


security_levels = (
    "Educational",
    "Research",
    "Classified Research",
    "Quantum Secure",
)


blocked_users = {
    "quantum_sim",
    "quantum_attack",
    "algorithm_theft",
}


def print_resources():

    print("\n" + "=" * 65)
    print("РЕСУРСИ СИСТЕМИ")
    print("=" * 65)

    print(f"{'Ресурс':<30}{'Рівень':<25}")
    print("-" * 65)

    for resource_name, security_level in resources:
        level_name = security_levels[security_level - 1]

        print(f"{resource_name:<30}{level_name:<25}")


def check_access(username, resource_level):
    """Перевіряє доступ користувача до ресурсу."""

    if username not in users:
        return "DENY", "User not found"

    if username in blocked_users:
        return "DENY", "User is blocked"

    user = users[username]

    if user["active"] is False:
        return "DENY", "Account inactive"

    if user["clearance"] >= resource_level:
        return "ALLOW", ""

    return "DENY", "Insufficient clearance"


def check_all_access():
    """Перевіряє доступ усіх користувачів до всіх ресурсів."""

    print("\n" + "=" * 65)
    print("РЕЗУЛЬТАТИ ПЕРЕВІРКИ ДОСТУПУ")
    print("=" * 65)

    for username in users:
        for resource_name, resource_level in resources:
            result, reason = check_access(
                username,
                resource_level,
            )

            if result == "ALLOW":
                print(
                    f"user={username} "
                    f"resource={resource_name} -> ALLOW"
                )
            else:
                print(
                    f"user={username} "
                    f"resource={resource_name} "
                    f"-> DENY ({reason})"
                )


def main():
    """Основна функція програми."""

    print(f"Студент: {STUDENT_NAME}")
    print(f"Група: {GROUP_NAME}")
    print(f"Варіант: {VARIANT_NUMBER}")

    print_resources()
    check_all_access()


if __name__ == "__main__":
    main()