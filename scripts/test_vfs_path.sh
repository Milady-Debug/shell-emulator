#!/bin/bash
# Тест: запуск с указанием VFS и стартового скрипта
python3 src/shell_emulator.py \
    --vfs-path vfs/vfs_deep.csv \
    --script-path scripts/script_default.txt