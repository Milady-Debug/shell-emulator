#!/bin/bash
# Тест: запуск с несуществующим CSV-файлом VFS
python3 src/shell_emulator.py \
    --vfs-path vfs/nonexistent.csv \
    --script-path scripts/script_default.txt