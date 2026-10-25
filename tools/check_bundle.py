#!/usr/bin/env python3
"""配布時のファイル一覧とSHA-256を確認する。真正性は信頼する配布経路で確認する。"""
from pathlib import Path, PurePosixPath
import hashlib
import sys

root=Path(__file__).resolve().parents[1]
manifest=root/'PACKAGE_CONTENTS.sha256'
if not manifest.is_file():
    raise SystemExit('配布時のPACKAGE_CONTENTS.sha256がありません。')
errors=[]; count=0
for line in manifest.read_text(encoding='utf-8').splitlines():
    expected,relative=line.split('  ',1)
    p=PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts or '\\' in relative:
        errors.append(f'不正な配布パス: {relative}'); continue
    file=root/relative
    if file.is_symlink() or not file.is_file():
        errors.append(f'ファイルがありません: {relative}'); continue
    if hashlib.sha256(file.read_bytes()).hexdigest()!=expected:
        errors.append(f'内容が異なります: {relative}')
    count+=1
if errors:
    print('\n'.join(errors),file=sys.stderr); raise SystemExit(1)
print(f'配布ファイル{count}件のSHA-256が一致しました。')
