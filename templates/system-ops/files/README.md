# {{system_name}}のシステム管理

システムID：`{{system_id}}`。
アプリ群の構成、調査、判断、移行計画、比較検証、継続保守の記録は、このリポジトリで管理する内容を基準とする。
初期状態はテンプレートの例。実repo、完全SHA、環境、承認者を調査して確定する。

## 最初に行うこと
`AGENTS.project.md` に個別条件を記入し、`system.yaml` に対象repo・アプリ・共通資源を登録する。
`repositories.lock.yaml` は解決済みSHAの一覧に更新し、その状態から調査Snapshotを作る。
調査指示は `.harness/prompts/investigate-only.md` を使う。

## 記録の配置
記録は、内容に応じて次の場所へ保存する。

- inventory：現在の知識
- investigations：run別の調査要約
- decisions：判断
- plans：作業分解
- verification：比較で守る条件（比較契約）と結果の要約
- maintenance：保守情報
- snapshots：固定構成
- deployments：実配備の観測

大きなログやDBは外部証跡ストアに置き、このrepoには保存先とhashを記録する。

## テンプレートの更新
適用版は `.harness/template.lock.json` に記録される。
配布元の `tools/template.py` で差分計画を作り、レビュー後に適用する。
個別設定と業務記録は導入先所有として保持する。
