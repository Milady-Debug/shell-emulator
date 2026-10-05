#!/bin/bash
# Тест: запуск с VFS, содержащей несколько файлов в корне
python3 src/shell_emulator.py \
    --vfs-path vfs/vfs_files.csv \
    --script-path scripts/script_default.txt
