"""Эмулятор командной строки UNIX-подобной ОС.

Этап 1. REPL с заглушками команд.
"""

import os
import socket
import sys


class ShellEmulator:
    """Эмулятор командной строки."""

    def __init__(self):
        """Создать эмулятор."""
        self.running = True

    def get_prompt(self):
        """Сформировать приглашение на основе данных ОС."""
        try:
            username = os.getlogin()
        except OSError:
            username = os.environ.get("USER") or "user"
        hostname = socket.gethostname()
        return f"{username}@{hostname}:~$ "

    def execute(self, command, args):
        """Выполнить команду."""
        if command == "ls":
            return f"Заглушка ls. Аргументы: {args}"
        if command == "cd":
            return f"Заглушка cd. Аргументы: {args}"
        if command == "exit":
            self.running = False
            return "Выход."
        if not command:
            return ""
        return f"Ошибка: неизвестная команда '{command}'"

    def run(self):
        """Запустить цикл REPL."""
        print("Добро пожаловать в эмулятор оболочки.")
        while self.running:
            try:
                line = input(self.get_prompt())
            except (EOFError, KeyboardInterrupt):
                print()
                break
            parts = line.strip().split()
            command = parts[0] if parts else ""
            args = parts[1:] if parts else []
            result = self.execute(command, args)
            if result:
                print(result)


def main():
    """Точка входа в приложение."""
    ShellEmulator().run()
    return 0


if __name__ == "__main__":
    sys.exit(main())