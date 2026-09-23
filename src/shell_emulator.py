"""Эмулятор командной строки UNIX-подобной ОС.

Этап 1. REPL — минимальный прототип с заглушками команд.
"""

import os
import socket
import sys


class ShellEmulator:
    """Эмулятор командной строки. Реализует цикл REPL."""

    def __init__(self, vfs_name: str = "VFS") -> None:
        """Создать эмулятор.

        Args:
            vfs_name: имя виртуальной файловой системы,
                отображаемое в приглашении к вводу.
        """
        self.vfs_name = vfs_name
        self.running = True

    def get_prompt(self) -> str:
        """Сформировать приглашение к вводу на основе данных ОС."""
        username = self._get_username()
        hostname = socket.gethostname()
        return f"{username}@{hostname}:~$ "

    @staticmethod
    def _get_username() -> str:
        """Получить имя текущего пользователя.

        os.getlogin() может выбросить исключение, если у процесса нет
        управляющего терминала. В этом случае используем переменные
        окружения как запасной вариант.
        """
        try:
            return os.getlogin()
        except OSError:
            return (
                    os.environ.get("USER")
                    or os.environ.get("USERNAME")
                    or "user"
            )

    @staticmethod
    def parse_command(line: str) -> tuple[str, list[str]]:
        """Разобрать строку на команду и аргументы по пробелам."""
        parts = line.strip().split()
        if not parts:
            return "", []
        return parts[0], parts[1:]

    def execute(self, command: str, args: list[str]) -> str:
        """Выполнить команду и вернуть строку с результатом."""
        if command == "ls":
            return self.cmd_ls(args)
        if command == "cd":
            return self.cmd_cd(args)
        if command == "exit":
            return self.cmd_exit(args)
        if command == "":
            return ""
        return f"Ошибка: неизвестная команда '{command}'"

    def cmd_ls(self, args: list[str]) -> str:
        """Заглушка команды ls."""
        return f"Заглушка ls. Аргументы: {args}"

    def cmd_cd(self, args: list[str]) -> str:
        """Заглушка команды cd."""
        return f"Заглушка cd. Аргументы: {args}"

    def cmd_exit(self, args: list[str]) -> str:
        """Завершить работу эмулятора."""
        self.running = False
        return "Выход из эмулятора."

    def run(self) -> None:
        """Запустить цикл REPL."""
        print(f"Добро пожаловать в эмулятор оболочки ({self.vfs_name}).")
        print("Введите 'exit' для выхода.")
        while self.running:
            try:
                line = input(self.get_prompt())
            except (EOFError, KeyboardInterrupt):
                print()
                break
            command, args = self.parse_command(line)
            result = self.execute(command, args)
            if result:
                print(result)


def main() -> int:
    """Точка входа в приложение."""
    emulator = ShellEmulator(vfs_name="VFS")
    emulator.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())