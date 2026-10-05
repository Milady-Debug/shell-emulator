#!/bin/bash
# Тест: запуск с глубоко вложенной VFS (≥ 3 уровней)
python3 src/shell_emulator.py \
    --vfs-path vfs/vfs_deep.csv \
    --script-path scripts/script_default.txt
