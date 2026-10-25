# アーキテクチャ

## 目的
システムの現在状態を根拠から説明し、必要な作業と検証へつなげる。
調査・照合・承認 → 計画 → 実装 → 検証 → 継続保守を、同じIDとSnapshotで追跡する。

## 中核の責務
| 構成 | 入力 | 出力・責務 |
|---|---|---|
| Workspace管理 | システム定義、repo lock | 固定ソース、Agentごとの読み取り領域 |
| Run管理 | Snapshot、プロンプト、能力宣言 | Run/Attempt、イベント、再開点、成果物digest |
| Agentアダプタ | 役割、許可操作、入力参照 | Claim、Evidence、Coverage、実行記録 |
| 照合 | 内容を確定し、以後変更しないA/B/C報告 | Finding、Unknown、Inventory案 |
| グラフ管理 | 型付き依存関係 | 変更影響、共有DBアクセス、互換性検証範囲 |
| 計画管理 | 承認Inventory、ADR | Workstream、Task DAG、ExecPlan |
| 環境Provider | 環境定義、操作計画 | 接続・起動・観測・条件付き復元 |
| 比較エンジン | シナリオ、初期状態、新旧観測 | 差分、判定、未検証範囲 |
| 保守管理 | 変更、障害、更新情報 | stale判定、差分再調査、回帰検証 |
| テンプレート管理 | 版付き配布物、導入先lock | 更新計画、競合、適用履歴 |

## モデルの関係
Systemには複数のRepository、Application、Component、Resourceが属する。
ApplicationとRepositoryは多対多とし、ソースの役割とpathを持つ。
Environmentは配置先、Deploymentは観測した成果物の組み合わせである。
Repository lockはソース構成、System Snapshotはソース・成果物・設定・データ条件の検証入力、Deploymentは実環境の観測状態を示す。
これらを分けることで、ソースが同じでも実配備WARが違うケースを検出する。

## 状態と履歴
Runは `created → investigating → reconciling → awaiting_approval → approved` を基本とする。
追加調査は `needs_followup`、失敗は `failed`、取り消しは `cancelled` として残す。
Attemptは再実行ごとに新しいIDを持ち、以前の出力と承認は当時のdigestを参照する。
Taskは `proposed → approved → ready → running → verifying → completed`、中断・失敗は `blocked / failed` とする。
現在のInventoryは、承認履歴から現在有効な内容を取り出して構成する。元のClaimとEvidenceはそのまま保ち、訂正を新しい版で追記する。

## 実装境界
型や参照の検証はコード、意味の調査はAgent、重要な判断と権限付与は人間が担当する。
Agentの文章上の自信と、根拠の強さは別々に記録する。
独立Agentはプロセス・コンテキスト・読み取り可能領域を分ける。同一モデルの複数実行は多様な視点を得る手段であり、統計的な独立性の保証とは別に評価する。
`agent-env` は将来の環境Provider候補とする。Providerに求める操作と能力の取り決めは、直接Compose/EC2 Providerでも満たせるようにする。
