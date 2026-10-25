#!/usr/bin/env python3
"""同梱契約データの形式・参照・タスクDAGを検査する。意味の真偽は別工程で確認する。"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
    import yaml
except ImportError as exc:
    raise SystemExit('検証用依存が必要です。許可された環境で requirements-dev.txt を導入してください。') from exc

ROOT = Path(__file__).resolve().parents[1]
COLLECTIONS = {
    'snapshots':'snapshot', 'runs':'run', 'evidence':'evidence', 'claims':'claim',
    'findings':'finding', 'dependencies':'dependency', 'decisions':'decision', 'tasks':'task',
    'scenarios':'scenario', 'observations':'observation', 'comparisons':'comparison',
    'accepted_differences':'accepted-difference', 'environments':'environment',
    'deployments':'deployment', 'approvals':'approval',
}
SINGLE = {'system':'system', 'repository_lock':'repository-lock', 'inventory':'inventory'}


def schema_errors(value: Any, name: str) -> list[str]:
    schema = json.loads((ROOT/'schemas'/f'{name}.schema.json').read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    errors = Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value)
    return [f'{name}:{"/".join(map(str,e.absolute_path)) or "/"}: {e.message}' for e in errors]


def cycle_errors(tasks: list[dict]) -> list[str]:
    index = {t['id']:t for t in tasks}
    active: list[str] = []
    done: set[str] = set()
    errors: list[str] = []
    def visit(tid: str) -> None:
        if tid in active:
            errors.append('タスク循環: ' + ' → '.join(active[active.index(tid):]+[tid]))
            return
        if tid in done or tid not in index:
            return
        active.append(tid)
        for dep in index[tid].get('depends_on', []):
            visit(dep)
        active.pop()
        done.add(tid)
    for tid in index:
        visit(tid)
    return errors


def validate_bundle(data: dict, ready: bool = False) -> list[str]:
    errors: list[str] = []
    expected = set(SINGLE) | set(COLLECTIONS) | {'schema_version','fixture','description'}
    if set(data) - expected:
        errors.append('未定義のデータ領域: ' + ', '.join(sorted(set(data)-expected)))
    for key,name in SINGLE.items():
        if key not in data:
            errors.append(f'必須データがありません: {key}')
        else:
            errors += schema_errors(data[key], name)
    for key,name in COLLECTIONS.items():
        if not isinstance(data.get(key, []), list):
            errors.append(f'配列を指定してください: {key}')
            continue
        for item in data.get(key, []):
            errors += schema_errors(item, name)
    if errors:
        return errors
    system=data['system']; sid=system['id']
    repos={r['id']:r for r in system['repositories']}
    nodes={n['id']:n for key in ('applications','components','resources') for n in system[key]}
    all_entities=[*system['repositories'],*(n for k in ('applications','components','resources') for n in system[k])]
    ids=[x['id'] for x in all_entities]
    if len(ids)!=len(set(ids)):
        errors.append('System内に重複Entity IDがあります')
    indexes={k:{x['id']:x for x in data.get(k,[])} for k in COLLECTIONS}
    global_ids=[sid,data['inventory']['id'],*ids]
    for key in COLLECTIONS:
        members=data.get(key,[])
        mids=[x['id'] for x in members]
        if len(mids)!=len(set(mids)):
            errors.append(f'重複ID: {key}')
        global_ids+=mids
        for item in members:
            if item['system_id']!=sid:
                errors.append(f'Systemの不一致: {item["id"]}')
    if len(global_ids)!=len(set(global_ids)):
        errors.append('データ全体に重複IDがあります')
    def ref(value: str | None, index: dict, context: str) -> None:
        if value is not None and value not in index:
            errors.append(f'参照先がありません: {context} → {value}')
    for group in ('applications','components'):
        for unit in system[group]:
            for src in unit['source_units']:
                ref(src['repository_id'],repos,unit['id'])
    lock=data['repository_lock']
    if lock['system_id']!=sid or data['inventory']['system_id']!=sid:
        errors.append('lockまたはInventoryのSystemが一致しません')
    lock_ids=[r['repository_id'] for r in lock['repositories']]
    if set(lock_ids)!=set(repos) or len(lock_ids)!=len(set(lock_ids)):
        errors.append('repository lockの対象集合がSystemと一致しません')
    for snap in data.get('snapshots',[]):
        for r in snap['repositories']:
            ref(r['repository_id'],repos,snap['id'])
        ref(snap['environment_id'],indexes['environments'],snap['id'])
    for key in ('runs','evidence','claims','findings','observations'):
        for item in data.get(key,[]):
            ref(item['snapshot_id'],indexes['snapshots'],item['id'])
    for ev in data.get('evidence',[]):
        loc=ev['locator']
        if loc['repository_id']:
            ref(loc['repository_id'],repos,ev['id'])
            snap=indexes['snapshots'].get(ev['snapshot_id'])
            if snap and loc['commit']:
                pins={r['repository_id']:r['commit'] for r in snap['repositories']}
                if pins.get(loc['repository_id'])!=loc['commit']:
                    errors.append(f'根拠とSnapshotのSHAが不一致: {ev["id"]}')
    for key,relations in {
        'claims':{'evidence_ids':'evidence'},
        'findings':{'claim_ids':'claims','evidence_ids':'evidence'},
        'dependencies':{'evidence_ids':'evidence'},
        'decisions':{'finding_ids':'findings'},
        'tasks':{'finding_ids':'findings','decision_ids':'decisions','depends_on':'tasks','verification_scenario_ids':'scenarios'},
        'observations':{'evidence_ids':'evidence'},
        'comparisons':{'accepted_difference_ids':'accepted_differences'},
        'deployments':{'evidence_ids':'evidence'},
    }.items():
        for item in data.get(key,[]):
            for field,target in relations.items():
                for item_id in item[field]:
                    ref(item_id,indexes[target],item['id'])
    for c in data.get('claims',[]):
        ref(c['run_id'],indexes['runs'],c['id']); ref(c['subject_id'],nodes,c['id'])
        run=indexes['runs'].get(c['run_id'])
        if run and run['snapshot_id']!=c['snapshot_id']:
            errors.append(f'ClaimとRunのSnapshotが不一致: {c["id"]}')
    for key in ('claims','findings'):
        for item in data.get(key,[]):
            for eid in item['evidence_ids']:
                ev=indexes['evidence'].get(eid)
                if ev and ev['snapshot_id']!=item['snapshot_id']:
                    errors.append(f'根拠と主張のSnapshotが不一致: {item["id"]}')
    for dep in data.get('dependencies',[]):
        ref(dep['consumer_id'],nodes,dep['id']); ref(dep['provider_id'],nodes,dep['id'])
    inv=data['inventory']
    ref(inv['snapshot_id'],indexes['snapshots'],inv['id'])
    for fid in inv['finding_ids']:
        ref(fid,indexes['findings'],inv['id'])
    all_index={i:True for i in global_ids}
    for key in ('decisions','accepted_differences'):
        for item in data.get(key,[]):
            ref(item['approval_id'],indexes['approvals'],item['id'])
            if item['status']=='approved' and item['approval_id'] is None:
                errors.append(f'承認済み項目にApprovalがありません: {item["id"]}')
    for a in data.get('approvals',[]):
        ref(a['subject_id'],all_index,a['id'])
    for task in data.get('tasks',[]):
        for rid in task['repository_ids']: ref(rid,repos,task['id'])
        if task['kind']=='implementation' and not task['decision_ids']:
            errors.append(f'実装Taskの判断根拠が不足: {task["id"]}')
        if task['status'] in ('ready','running','verifying','completed'):
            for did in task['decision_ids']:
                decision=indexes['decisions'].get(did)
                if decision and decision['status']!='approved':
                    errors.append(f'未承認Decisionに依存する実行可能Task: {task["id"]}')
    errors+=cycle_errors(data.get('tasks',[]))
    for key in ('observations','comparisons','accepted_differences'):
        for item in data.get(key,[]): ref(item['scenario_id'],indexes['scenarios'],item['id'])
    for cmp in data.get('comparisons',[]):
        for field in ('legacy_observation_id','modern_observation_id'):
            ref(cmp[field],indexes['observations'],cmp['id'])
        old=indexes['observations'].get(cmp['legacy_observation_id']); new=indexes['observations'].get(cmp['modern_observation_id'])
        if old and new:
            if old['scenario_id']!=cmp['scenario_id'] or new['scenario_id']!=cmp['scenario_id']:
                errors.append(f'比較Scenarioが不一致: {cmp["id"]}')
            if cmp['result'] in ('equivalent','accepted_difference') and (not old['completed'] or not new['completed'] or old['initial_state_digest']!=new['initial_state_digest']):
                errors.append(f'比較前提が不足しています: {cmp["id"]}')
        if cmp['result']=='accepted_difference' and not cmp['accepted_difference_ids']:
            errors.append(f'意図差の承認参照がありません: {cmp["id"]}')
    for env in data.get('environments',[]):
        if env['classification']=='production' and ('reset' in env['capabilities'] or any(op in env['allowed_operations'] for op in ('reset','seed','fault-injection'))):
            errors.append(f'本番環境に隔離検証用の能力が宣言されています: {env["id"]}')
    for dep in data.get('deployments',[]):
        ref(dep['environment_id'],indexes['environments'],dep['id'])
    if ready:
        if data.get('fixture'):
            errors.append('架空fixtureは実調査のready入力には使えません')
        if system['readiness']!='ready' or lock['readiness']!='ready':
            errors.append('Systemとlockがreadyではありません')
        if any(r['commit'] is None for r in lock['repositories']):
            errors.append('未解決のcommitがあります')
        if any('example.invalid' in r['url'] for r in system['repositories']):
            errors.append('repo URLが説明用の値です')
    return errors


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('path',type=Path)
    p.add_argument('--schema',help='単一ファイルのschema名。省略するとbundleを検査する')
    p.add_argument('--ready',action='store_true',help='bundleが実調査入力の基本条件を満たすか確認する')
    a=p.parse_args()
    try:
        data=yaml.safe_load(a.path.read_text(encoding='utf-8'))
        if a.schema:
            if a.schema not in {f.name.removesuffix('.schema.json') for f in (ROOT/'schemas').glob('*.schema.json')}:
                raise ValueError('存在するschema名を指定してください')
            errors=schema_errors(data,a.schema)
        else:
            errors=validate_bundle(data,ready=a.ready)
        if errors:
            print('\n'.join(errors),file=sys.stderr); return 1
        print('検証成功。主張の真偽と実環境の安全性は別工程で確認してください。'); return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(f'検証エラー: {exc}',file=sys.stderr); return 2

if __name__=='__main__':
    raise SystemExit(main())
