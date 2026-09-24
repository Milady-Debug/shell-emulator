"""Эмулятор командной строки UNIX-подобной ОС.

Этап 2. Конфигурация: аргументы командной строки и стартовый скрипт.
"""

import argparse
import os
import socket
import sys


class ShellEmulator:
    """Эмулятор командной строки. Реализует цикл REPL."""

    def __init__(
        self,
        vfs_path: str | None = None,
        script_path: str | None = None,
    ) -> None:
        """Создать эмулятор.

        Args:
            vfs_path: путь к файлу виртуальной файловой системы.
            script_path: путь к стартовому скрипту с командами.
        """
        self.vfs_path = vfs_path
        self.script_path = script_path
        self.running = True

    # ---------- Приглашение и парсер ----------

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

    # ---------- Отладочный вывод параметров ----------

    def dump_config(self) -> None:
        """Вывести отладочную информацию о параметрах запуска."""
        print("=== Параметры эмулятора ===")
        print(f"vfs_path    = {self.vfs_path!r}")
        print(f"script_path = {self.script_path!r}")
        print("===========================")

    # ---------- Диспетчер команд ----------

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

    # ---------- Выполнение стартового скрипта ----------

    def run_script(self, path: str) -> None:
        """Выполнить команды из стартового скрипта.

        Ошибочные строки пропускаются, выполнение продолжается.
        На экран выводится имитация диалога: приглашение + команда
        + результат.
        """
        try:
            with open(path, "r", encoding="utf-8") as handle:
                lines = handle.readlines()
        except FileNotFoundError:
            print(f"Ошибка: стартовый скрипт '{path}' не найден.")
            return

        for raw in lines:
            line = raw.rstrip("\n")
            stripped = line.strip()
            # Пропускаем пустые строки и комментарии.
            if not stripped or stripped.startswith("#"):
                continue
            print(f"{self.get_prompt()}{line}")
            try:
                command, args = self.parse_command(line)
                result = self.execute(command, args)
            except Exception as error:  # noqa: BLE001
                print(f"Ошибка при выполнении '{line}': {error}")
                continue
            if result:
                print(result)
            # Если команда была exit — прекращаем выполнение скрипта.
            if not self.running:
                break

    # ---------- Основной цикл ----------

    def run(self) -> None:
        """Запустить цикл REPL."""
        self.dump_config()
        if self.script_path:
            print(f"Выполняется стартовый скрипт: {self.script_path}")
            self.run_script(self.script_path)
            if not self.running:
                return
        print("Добро пожаловать в эмулятор оболочки.")
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


# ---------- Точка входа ----------

def build_arg_parser() -> argparse.ArgumentParser:
    """Собрать парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="shell_emulator",
        description="Эмулятор командной строки UNIX-подобной ОС.",
    )
    parser.add_argument(
        "--vfs-path",
        dest="vfs_path",
        default=None,
        help="Путь к CSV-файлу виртуальной файловой системы.",
    )
    parser.add_argument(
        "--script-path",
        dest="script_path",
        default=None,
        help="Путь к стартовому скрипту с командами.",
    )
    return parser


def main() -> int:
    """Точка входа в приложение."""
    args = build_arg_parser().parse_args()
    emulator = ShellEmulator(
        vfs_path=args.vfs_path,
        script_path=args.script_path,
    )
    emulator.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
