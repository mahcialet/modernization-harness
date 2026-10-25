#!/usr/bin/env python3
"""版付きテンプレートのローカル生成と、レビューを経た更新。外部コマンドは実行しない。"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
from typing import Any

LOCK = '.harness/template.lock.json'
TOKEN = re.compile(r'\{\{([a-z][a-z0-9_]*)\}\}')
VERSION = re.compile(r'^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$')
RESERVED = ('.git', '.harness/template-base', LOCK, '.harness/template-update.lock')


class TemplateError(Exception):
    """利用者が入力と計画を確認できる検証エラー。"""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(data: Any) -> bytes:
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise TemplateError(f'JSONを読み取れません: {path}: {exc}') from exc


def relpath(value: str, *, internal: bool = False) -> str:
    if not isinstance(value, str) or not value or '\\' in value or ':' in value or '\x00' in value:
        raise TemplateError(f'安全な相対パスを指定してください: {value!r}')
    parts = value.split('/')
    if value.startswith('/') or any(p in ('', '.', '..') for p in parts):
        raise TemplateError(f'パスの外部参照を検出しました: {value!r}')
    if any(p.casefold() == '.git' for p in parts):
        raise TemplateError('Git管理領域は対象外です')
    if not internal and any(value == x or value.startswith(x + '/') for x in RESERVED):
        raise TemplateError(f'予約済み領域です: {value}')
    return value


def rooted(root: Path, relative: str, *, internal: bool = False) -> Path:
    relpath(relative, internal=internal)
    if root.is_symlink():
        raise TemplateError(f'実体ディレクトリを指定してください: {root}')
    result = root
    for part in PurePosixPath(relative).parts:
        result = result / part
        if result.is_symlink():
            raise TemplateError(f'シンボリックリンクは対象外です: {result}')
    return result


def content(path: Path) -> bytes | None:
    if path.is_symlink():
        raise TemplateError(f'シンボリックリンクは対象外です: {path}')
    if path.exists() and not path.is_file():
        raise TemplateError(f'通常ファイルを想定しています: {path}')
    return path.read_bytes() if path.exists() else None


def sha_or_none(data: bytes | None) -> str | None:
    return None if data is None else digest(data)


def version(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str) or not VERSION.fullmatch(value):
        raise TemplateError(f'版はX.Y.Z形式で指定してください: {value!r}')
    return tuple(map(int, value.split('.')))  # type: ignore[return-value]


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.template-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def read_template(source: Path, values: dict[str, str]) -> tuple[dict, dict[str, bytes], dict]:
    source = source.absolute()
    manifest = load_json(rooted(source, 'template.json'))
    version(manifest['template_version'])
    params = manifest.get('parameters', {})
    if set(params) != set(values):
        raise TemplateError(f'変数を一致させてください。必要={sorted(params)} 指定={sorted(values)}')
    context: dict[str, str] = {}
    for key, rules in params.items():
        val = values[key]
        if not isinstance(val, str) or not val or len(val) > 1000 or '\x00' in val or '\n' in val or '\r' in val:
            raise TemplateError(f'変数は空でない1行の文字列です: {key}')
        if rules.get('pattern') and not re.fullmatch(rules['pattern'], val):
            raise TemplateError(f'変数の形式が一致しません: {key}')
        context[key] = val
        context[key + '_json'] = json.dumps(val, ensure_ascii=False)
    rendered: dict[str, bytes] = {}
    raw_hashes: dict[str, str] = {}
    files: dict[str, dict] = {}
    seen: set[str] = set()
    for entry in manifest['files']:
        p = relpath(entry['path'])
        if p.casefold() in seen:
            raise TemplateError(f'大文字小文字を含め重複パスがあります: {p}')
        seen.add(p.casefold())
        if entry['ownership'] not in ('managed', 'seed'):
            raise TemplateError(f'所有権が不明です: {p}')
        raw = rooted(source, 'files/' + p).read_bytes()
        text = raw.decode('utf-8')
        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            if key not in context:
                raise TemplateError(f'未定義の変数です: {key} ({p})')
            return context[key]
        result = TOKEN.sub(replace, text).encode('utf-8')
        rendered[p] = result
        raw_hashes[p] = digest(raw)
        files[p] = {'ownership': entry['ownership'], 'base_sha256': digest(result)}
    source_digest = digest(encode({'manifest': manifest, 'files': raw_hashes}))
    lock = {
        'schema_version': manifest['schema_version'],
        'template_id': manifest['template_id'],
        'template_version': manifest['template_version'],
        'template_digest': source_digest,
        'source_release_tag': manifest.get('source_release_tag'),
        'source_commit': manifest.get('source_commit'),
        'source_kind': 'local-bundle',
        'values': values,
        'base_dir': '.harness/template-base/' + source_digest,
        'files': files,
    }
    return lock, rendered, manifest


def read_lock(target: Path) -> tuple[dict, bytes]:
    raw = content(rooted(target, LOCK, internal=True))
    if raw is None:
        raise TemplateError(f'導入版のlockがありません: {target}')
    lock = json.loads(raw)
    version(lock['template_version'])
    expected = '.harness/template-base/' + lock['template_digest']
    if not re.fullmatch(r'[0-9a-f]{64}', lock['template_digest']) or lock['base_dir'] != expected:
        raise TemplateError('基準ディレクトリとdigestが不一致です')
    seen: set[str] = set()
    for p, meta in lock['files'].items():
        relpath(p)
        if p.casefold() in seen:
            raise TemplateError(f'lockに重複パスがあります: {p}')
        seen.add(p.casefold())
        base = content(rooted(target, lock['base_dir'] + '/' + p, internal=True))
        if base is None or digest(base) != meta['base_sha256']:
            raise TemplateError(f'適用基準が変更または欠落しています: {p}')
    return lock, raw


def init(source: Path, values: dict, destination: Path) -> dict:
    destination = destination.absolute()
    if destination.is_symlink():
        raise TemplateError('出力先は実体ディレクトリにしてください')
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise TemplateError('初期化先は新規または空のディレクトリにしてください')
    lock, rendered, _ = read_template(source, values)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.template-init-', dir=destination.parent))
    try:
        for p, data in rendered.items():
            atomic_write(rooted(staging, p), data)
            atomic_write(rooted(staging, lock['base_dir'] + '/' + p, internal=True), data)
        atomic_write(rooted(staging, LOCK, internal=True), encode(lock))
        if destination.exists():
            destination.rmdir()
        staging.rename(destination)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return lock


def save_plan(directory: Path, plan: dict) -> str:
    data = encode(plan)
    atomic_write(rooted(directory, 'plan.json'), data)
    checksum = digest(data)
    atomic_write(rooted(directory, 'plan.sha256'), (checksum + '\n').encode())
    rows = ['# テンプレート更新レビュー', '', f"対象：`{plan['target']}`", '',
            f"新しい版：`{plan['new_lock']['template_version']}`", '',
            f'承認対象SHA-256：`{checksum}`', '',
            '| パス | 操作 | 理由 |', '|---|---|---|']
    for a in plan['actions']:
        rows.append(f"| `{a['path']}` | `{a['action']}` | {a['reason']} |")
    rows += ['', '`incoming/`は新配布基準、`candidate/`は適用する内容、`conflicts/`は競合の旧基準と現在内容。',
             'seedの既存内容は保持する。競合はresolveで採用結果を明示する。',
             '変更後は新しいplan.sha256を確認し、applyへ渡す。', '']
    atomic_write(rooted(directory, 'review.md'), '\n'.join(rows).encode('utf-8'))
    return checksum


def plan_update(target: Path, source: Path, output: Path) -> dict:
    target, output = target.absolute(), output.absolute()
    if output == target or target in output.parents:
        raise TemplateError('レビュー出力は対象リポジトリの外に置いてください')
    if output.exists():
        raise TemplateError('レビュー出力先は新しいディレクトリにしてください')
    old, old_raw = read_lock(target)
    new, incoming, _ = read_template(source, old['values'])
    if old['template_id'] != new['template_id']:
        raise TemplateError('テンプレートIDが異なります')
    if old['schema_version'] != new['schema_version']:
        raise TemplateError('schema版変更には専用のmigration計画を作成してください')
    if version(new['template_version']) < version(old['template_version']):
        raise TemplateError('旧版への復旧はGitの承認済みコミットを使ってください')
    if new['template_version'] == old['template_version'] and new['template_digest'] != old['template_digest']:
        raise TemplateError('同じ版の配布内容が変わっています。新しい版を発行してください')
    actions: list[dict] = []
    candidates: dict[str, bytes] = {}
    conflicts: dict[str, tuple[bytes | None, bytes | None]] = {}
    diffs: list[str] = []
    paths = set(old['files']) | set(new['files'])
    if len({p.casefold() for p in paths}) != len(paths):
        raise TemplateError('大文字小文字だけが異なるパス変更は個別の移行で扱ってください')
    for p in sorted(paths):
        before, after = old['files'].get(p), new['files'].get(p)
        local = content(rooted(target, p))
        base = content(rooted(target, old['base_dir'] + '/' + p, internal=True)) if before else None
        nxt = incoming.get(p)
        action, reason = 'keep', '現在の内容を保持する。'
        if after and after['ownership'] == 'seed':
            if not before and local is None:
                action, reason = 'add', '新しい初期設定ファイルを追加する。'
            else:
                action, reason = 'seed_keep', '導入先所有の設定を保持し、新雛形は参考差分として示す。'
        elif before and before['ownership'] == 'seed':
            if after:
                action, reason = 'conflict', 'seedから共通管理への所有権変更を確認する。'
            else:
                action, reason = 'keep', '配布対象外になった個別設定を保持する。'
        elif after is None:
            if local is None:
                action, reason = 'keep', '既に存在しない配布ファイルを管理対象から外す。'
            elif local == base:
                action, reason = 'delete', '未編集の旧配布ファイルを削除する。'
            else:
                action, reason = 'conflict', '配布元で削除され、導入先で編集されたファイルを確認する。'
        elif before is None:
            if local is None:
                action, reason = 'add', '新しい共通ファイルを追加する。'
            elif local == nxt:
                action, reason = 'keep', '同じ内容を共通管理対象に登録する。'
            else:
                action, reason = 'conflict', '新しい配布ファイルと既存ファイルの衝突を確認する。'
        elif local == nxt or nxt == base:
            action, reason = 'keep', '配布側の変更がないか、既に一致しているため保持する。'
        elif local == base:
            action, reason = 'update', '導入先未編集のファイルへ新配布内容を適用する。'
        else:
            action, reason = 'conflict', '配布元と導入先の両側変更を確認する。'
        candidate_sha = None
        if action in ('add', 'update'):
            assert nxt is not None
            candidates[p] = nxt
            candidate_sha = digest(nxt)
        if action == 'conflict':
            conflicts[p] = (base, local)
        actions.append({'path': p, 'action': action, 'expected_sha256': sha_or_none(local),
                        'incoming_sha256': sha_or_none(nxt), 'candidate_sha256': candidate_sha,
                        'reason': reason})
        if base != nxt:
            diffs.extend(difflib.unified_diff((base or b'').decode('utf-8').splitlines(True),
                         (nxt or b'').decode('utf-8').splitlines(True),
                         fromfile='old-template/' + p, tofile='new-template/' + p))
    plan = {'schema_version': '0.1.0', 'target': str(target), 'old_lock_sha256': digest(old_raw),
            'new_lock': new, 'actions': actions,
            'incoming_sha256': {p: digest(b) for p, b in incoming.items()}}
    output.mkdir(parents=True)
    try:
        for p, data in incoming.items():
            atomic_write(rooted(output, 'incoming/' + p, internal=True), data)
        for p, data in candidates.items():
            atomic_write(rooted(output, 'candidate/' + p, internal=True), data)
        for p, (base, local) in conflicts.items():
            if base is not None:
                atomic_write(rooted(output, 'conflicts/base/' + p, internal=True), base)
            if local is not None:
                atomic_write(rooted(output, 'conflicts/local/' + p, internal=True), local)
        atomic_write(rooted(output, 'upstream.diff'), ''.join(diffs).encode('utf-8'))
        save_plan(output, plan)
    except Exception:
        shutil.rmtree(output, ignore_errors=True)
        raise
    return plan


def resolve(directory: Path, path: str, choice: str, file: Path | None) -> str:
    relpath(path)
    plan = load_json(rooted(directory, 'plan.json'))
    matches = [a for a in plan['actions'] if a['path'] == path]
    if len(matches) != 1 or matches[0]['action'] != 'conflict':
        raise TemplateError('未解決の競合パスを指定してください')
    a = matches[0]
    if choice == 'keep-local':
        a['action'], a['candidate_sha256'] = 'keep', None
    elif choice == 'use-incoming':
        data = content(rooted(directory, 'incoming/' + path, internal=True))
        if data is None:
            a['action'], a['candidate_sha256'] = 'delete', None
        else:
            if digest(data) != a['incoming_sha256']:
                raise TemplateError('incomingの内容が変更されています')
            atomic_write(rooted(directory, 'candidate/' + path, internal=True), data)
            a['action'], a['candidate_sha256'] = 'update', digest(data)
    elif choice == 'file':
        if file is None:
            raise TemplateError('--fileで採用するファイルを指定してください')
        data = content(file)
        if data is None:
            raise TemplateError('採用ファイルが見つかりません')
        data.decode('utf-8')
        atomic_write(rooted(directory, 'candidate/' + path, internal=True), data)
        a['action'], a['candidate_sha256'] = 'update', digest(data)
    else:
        raise TemplateError('解決方法が不明です')
    a['reason'] = f'作業者が競合の採用結果を指定した: {choice}'
    return save_plan(directory, plan)


def apply(directory: Path, approval: str) -> dict:
    raw = rooted(directory, 'plan.json').read_bytes()
    if digest(raw) != approval:
        raise TemplateError('承認digestが現在の計画と一致しません')
    plan = json.loads(raw)
    target = Path(plan['target'])
    old, old_raw = read_lock(target)
    if digest(old_raw) != plan['old_lock_sha256']:
        raise TemplateError('計画後に導入先lockが変更されています')
    new = plan['new_lock']
    if new['template_id'] != old['template_id']:
        raise TemplateError('テンプレートIDが一致しません')
    if new['base_dir'] != '.harness/template-base/' + new['template_digest'] or not re.fullmatch(r'[0-9a-f]{64}', new['template_digest']):
        raise TemplateError('新しい基準領域が不正です')
    if any(a['action'] == 'conflict' for a in plan['actions']):
        raise TemplateError('未解決の競合があります。resolveで採用結果を明示してください')
    union = set(old['files']) | set(new['files'])
    actions = plan['actions']
    if len(actions) != len(union) or {a['path'] for a in actions} != union:
        raise TemplateError('変更計画の対象がlockと一致しません')
    writes: dict[str, bytes | None] = {}
    for a in actions:
        p = relpath(a['path'])
        if sha_or_none(content(rooted(target, p))) != a['expected_sha256']:
            raise TemplateError(f'計画後に変更されています。計画を再作成してください: {p}')
        if a['action'] in ('add', 'update'):
            data = content(rooted(directory, 'candidate/' + p, internal=True))
            if data is None or digest(data) != a['candidate_sha256']:
                raise TemplateError(f'適用候補が改変されています: {p}')
            writes[p] = data
        elif a['action'] == 'delete':
            writes[p] = None
        elif a['action'] not in ('keep', 'seed_keep'):
            raise TemplateError(f'未定義の操作です: {a["action"]}')
    if set(plan['incoming_sha256']) != set(new['files']):
        raise TemplateError('incomingと新lockの一覧が一致しません')
    for p, meta in new['files'].items():
        relpath(p)
        data = content(rooted(directory, 'incoming/' + p, internal=True))
        if data is None or digest(data) != meta['base_sha256'] or digest(data) != plan['incoming_sha256'][p]:
            raise TemplateError(f'新しい基準の内容が不一致です: {p}')
        base_path = new['base_dir'] + '/' + p
        existing = content(rooted(target, base_path, internal=True))
        if existing is not None and existing != data:
            raise TemplateError(f'同じdigestの基準が異なる内容です: {p}')
        if existing is None:
            writes[base_path] = data
    writes[LOCK] = encode(new)
    guard = rooted(target, '.harness/template-update.lock', internal=True)
    guard.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(guard, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise TemplateError('別の更新が実行中か、前回の更新記録が残っています') from exc
    os.close(fd)
    backups: dict[str, bytes | None] = {}
    applied: list[str] = []
    try:
        for p in writes:
            backups[p] = content(rooted(target, p, internal=True))
        for p, data in writes.items():
            dest = rooted(target, p, internal=True)
            applied.append(p)
            if data is None:
                dest.unlink(missing_ok=True)
            else:
                atomic_write(dest, data)
    except Exception:
        for p in reversed(applied):
            dest = rooted(target, p, internal=True)
            if backups[p] is None:
                dest.unlink(missing_ok=True)
            else:
                atomic_write(dest, backups[p])  # type: ignore[arg-type]
        raise
    finally:
        guard.unlink(missing_ok=True)
    return new


def status(target: Path) -> dict:
    lock, _ = read_lock(target)
    rows = []
    for p, meta in sorted(lock['files'].items()):
        current = content(rooted(target, p))
        rows.append({'path': p, 'ownership': meta['ownership'],
                     'state': 'missing' if current is None else ('unchanged' if digest(current) == meta['base_sha256'] else 'modified')})
    return {'template_id': lock['template_id'], 'template_version': lock['template_version'],
            'template_digest': lock['template_digest'], 'files': rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('init', help='新規導入先を生成する')
    p.add_argument('--template', type=Path, required=True)
    p.add_argument('--values', type=Path, required=True)
    p.add_argument('--destination', type=Path, required=True)
    p = sub.add_parser('status', help='版と独自変更を表示する')
    p.add_argument('--target', type=Path, required=True)
    p = sub.add_parser('plan', help='導入先を変えず更新計画を生成する')
    p.add_argument('--target', type=Path, required=True)
    p.add_argument('--template', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('resolve', help='競合の採用結果を指定する')
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--path', required=True)
    p.add_argument('--choice', choices=['keep-local', 'use-incoming', 'file'], required=True)
    p.add_argument('--file', type=Path)
    p = sub.add_parser('apply', help='レビューした計画をdigest付きで適用する')
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--approve', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            result = init(args.template, load_json(args.values), args.destination)
            print(f'生成しました: {args.destination} (版 {result["template_version"]})')
        elif args.command == 'status':
            print(encode(status(args.target)).decode('utf-8'), end='')
        elif args.command == 'plan':
            plan_update(args.target, args.template, args.output)
            print(f'更新計画: {args.output / "review.md"}')
            print('承認対象digest:', (args.output / 'plan.sha256').read_text().strip())
        elif args.command == 'resolve':
            print('新しい承認対象digest:', resolve(args.plan, args.path, args.choice, args.file))
        elif args.command == 'apply':
            result = apply(args.plan, args.approve)
            print(f'適用しました: {result["template_version"]}。Git差分とテストを確認してください。')
        return 0
    except (TemplateError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f'エラー: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
