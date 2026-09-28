"""Эмулятор командной строки UNIX-подобной ОС.

Этап 4. Реальные команды ls, cd, tree, cal, uname.
"""

import argparse
import base64
import calendar
import csv
import os
import platform
import socket
import sys
from datetime import datetime


class VFSNode:
    """Узел виртуальной файловой системы."""

    def __init__(
        self,
        name: str,
        is_dir: bool = True,
        content: bytes | None = None,
    ) -> None:
        """Создать узел.

        Args:
            name: имя файла или каталога.
            is_dir: True для каталога, False для файла.
            content: содержимое файла (bytes) или None.
        """
        self.name = name
        self.is_dir = is_dir
        self.content = content
        self.children: dict[str, "VFSNode"] = {}

    def add_child(self, node: "VFSNode") -> None:
        """Добавить дочерний узел."""
        self.children[node.name] = node


class VFS:
    """Виртуальная файловая система в памяти."""

    def __init__(self, name: str = "VFS") -> None:
        """Создать пустую VFS с корневым каталогом."""
        self.name = name
        self.root = VFSNode("/", is_dir=True)
        self.current_dir = self.root

    def load_from_csv(self, path: str) -> None:
        """Загрузить VFS из CSV-файла.

        Формат строки: path, is_dir,content_base64.
        Вложенность восстанавливается из полного пути.
        """
        with open(path, "r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                self._add_from_row(row)

    def _add_from_row(self, row: dict[str, str]) -> None:
        """Добавить узел в дерево на основе строки CSV."""
        raw_path = row.get("path") or ""
        path = raw_path.strip()
        is_dir = (row.get("is_dir") or "").strip() == "1"
        content_b64 = (row.get("content_base64") or "").strip()

        content = None
        if content_b64:
            content = base64.b64decode(content_b64)

        parts = [p for p in path.split("/") if p]
        current = self.root
        for index, part in enumerate(parts):
            is_last = index == len(parts) - 1
            if part not in current.children:
                node = VFSNode(
                    name=part,
                    is_dir=is_dir if is_last else True,
                    content=content if is_last else None,
                )
                current.add_child(node)
            current = current.children[part]

    def count_nodes(self) -> int:
        """Подсчитать количество узлов, кроме корня."""
        return self._count_children(self.root)

    def _count_children(self, node: VFSNode) -> int:
        """Рекурсивно подсчитать всех потомков узла."""
        total = len(node.children)
        for child in node.children.values():
            total += self._count_children(child)
        return total


class ShellEmulator:
    """Эмулятор командной строки. Реализует цикл REPL."""

    def __init__(
        self,
        vfs_path: str | None = None,
        script_path: str | None = None,
        vfs_name: str = "VFS",
    ) -> None:
        """Создать эмулятор.

        Args:
            vfs_path: путь к CSV-файлу виртуальной ФС.
            script_path: путь к стартовому скрипту.
            vfs_name: имя виртуальной ФС.
        """
        self.vfs_path = vfs_path
        self.script_path = script_path
        self.vfs = VFS(name=vfs_name)
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

    # ---------- Загрузка VFS ----------

    def _load_vfs(self) -> None:
        """Загрузить VFS из файла, если указан путь."""
        if not self.vfs_path:
            return
        try:
            self.vfs.load_from_csv(self.vfs_path)
        except FileNotFoundError:
            print(
                f"Ошибка: файл VFS '{self.vfs_path}' не найден. "
                "Используется пустая VFS."
            )
        except (csv.Error, ValueError) as error:
            print(f"Ошибка загрузки VFS '{self.vfs_path}': {error}")

    # ---------- Отладочный вывод параметров ----------

    def dump_config(self) -> None:
        """Вывести отладочную информацию о параметрах запуска."""
        print("=== Параметры эмулятора ===")
        print(f"vfs_path    = {self.vfs_path!r}")
        print(f"script_path = {self.script_path!r}")
        print(f"vfs_name    = {self.vfs.name!r}")
        print(f"vfs_nodes   = {self.vfs.count_nodes()}")
        print("===========================")

    # ---------- Диспетчер команд ----------

    def execute(self, command: str, args: list[str]) -> str:
        """Выполнить команду и вернуть строку с результатом."""
        if command == "ls":
            return self.cmd_ls(args)
        if command == "cd":
            return self.cmd_cd(args)
        if command == "tree":
            return self.cmd_tree(args)
        if command == "cal":
            return self.cmd_cal(args)
        if command == "uname":
            return self.cmd_uname(args)
        if command == "exit":
            return self.cmd_exit(args)
        if command == "":
            return ""
        return f"Ошибка: неизвестная команда '{command}'"

    # ---------- Команда ls ----------

    def cmd_ls(self, args: list[str]) -> str:
        """Вывести содержимое текущего каталога.

        Абсолютные пути не поддерживаются. Если переданы лишние
        аргументы — выводится предупреждение.
        """
        if args:
            return (
                "Ошибка: ls не поддерживает аргументы в этой версии. "
                f"Получено: {args}"
            )
        names = sorted(self.vfs.current_dir.children.keys())
        if not names:
            return ""
        return "\n".join(names)

    # ---------- Команда cd ----------

    def cmd_cd(self, args: list[str]) -> str:
        """Перейти в подкаталог текущего каталога.

        - без аргументов или `..` — переход в корень VFS;
        - `<имя>` — переход в подкаталог, если он существует.
        """
        if not args or args[0] == "..":
            self.vfs.current_dir = self.vfs.root
            return ""
        if len(args) > 1:
            return f"Ошибка: cd принимает один аргумент, получено {args}"
        target = args[0]
        children = self.vfs.current_dir.children
        if target not in children:
            return f"Ошибка: каталог '{target}' не найден."
        node = children[target]
        if not node.is_dir:
            return f"Ошибка: '{target}' не является каталогом."
        self.vfs.current_dir = node
        return ""

    # ---------- Команда tree ----------

    def cmd_tree(self, args: list[str]) -> str:
        """Вывести дерево текущего каталога.

        Рекурсивный обход с символами ├── и └──.
        """
        if args:
            return f"Ошибка: tree не принимает аргументов, получено: {args}"
        lines = self._tree_lines(self.vfs.current_dir)
        if not lines:
            return "."
        return "\n".join(lines)

    def _tree_lines(
        self,
        node: VFSNode,
        prefix: str = "",
    ) -> list[str]:
        """Сформировать строки дерева для узла и его потомков."""
        lines: list[str] = []
        children = sorted(node.children.values(), key=lambda n: n.name)
        for index, child in enumerate(children):
            is_last = index == len(children) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{child.name}")
            if child.is_dir and child.children:
                extension = "    " if is_last else "│   "
                lines.extend(self._tree_lines(child, prefix + extension))
        return lines

    # ---------- Команда cal ----------

    def cmd_cal(self, args: list[str]) -> str:
        """Вывести календарь на текущий месяц."""
        if args:
            return f"Ошибка: cal не принимает аргументов, получено: {args}"
        now = datetime.now()
        return calendar.month(now.year, now.month)

    # ---------- Команда uname ----------

    def cmd_uname(self, args: list[str]) -> str:
        """Вывести информацию о системе."""
        if args:
            return f"Ошибка: uname не принимает аргументов, получено: {args}"
        system = platform.system()
        release = platform.release()
        return f"{system} {release}"

    # ---------- Команда exit ----------

    def cmd_exit(self, args: list[str]) -> str:
        """Завершить работу эмулятора."""
        self.running = False
        return "Выход из эмулятора."

    # ---------- Выполнение стартового скрипта ----------

    def run_script(self, path: str) -> None:
        """Выполнить команды из стартового скрипта.

        Ошибочные строки пропускаются, выполнение продолжается.
        На экран выводится имитация диалога.
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
            if not self.running:
                break

    # ---------- Основной цикл ----------

    def run(self) -> None:
        """Запустить цикл REPL."""
        self._load_vfs()
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
