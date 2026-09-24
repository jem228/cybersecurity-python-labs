from labs.lab01.task1 import main as task1_main
from labs.lab01.task2 import main as task2_main
from labs.lab01.task3 import main as task3_main
from shared.student import (
    GROUP_NAME,
    STUDENT_NAME,
    VARIANT_NUMBER,
)


def main():
    print("-" * 100)
    print("ЛАБОРАТОРНА РОБОТА №1")
    print("-" * 100)

    print(f"Студент: {STUDENT_NAME}")
    print(f"Група: {GROUP_NAME}")
    print(f"Варіант: {VARIANT_NUMBER}")

    
    print("\nTask 1")
    print("-" * 100)
    task1_main()

    
    print("\nTask 2")
    print("-" * 100)
    task2_main()

    
    print("\nTask 3")
    print("-" * 100)
    task3_main()


if __name__ == "__main__":
    main()