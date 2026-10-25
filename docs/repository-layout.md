# リポジトリと作業領域

## 3層の所有権

```text
workspace/                           ← このディレクトリ全体はGit管理しない
├── modernization-harness/            ← 配布元Gitリポジトリ
│   ├── schemas/ agents/ workflows/
│   ├── templates/system-ops/
│   ├── templates/application-overlay/
│   └── tools/ tests/ docs/
├── order-system-ops/                 ← システム管理Gitリポジトリ
│   ├── system.yaml
│   ├── repositories.lock.yaml
│   ├── .harness/template.lock.json
│   ├── inventory/ investigations/ decisions/ plans/
│   ├── verification/ environments/ maintenance/
│   └── snapshots/ deployments/
├── repositories/                    ← 開発者の通常clone。既存履歴を維持
│   ├── order-web/.git/
│   ├── order-batch/.git/
│   └── order-common/.git/
└── work/                            ← ハーネスが確保する再生成可能な領域
    └── RUN-.../
        ├── investigator-a/{order-web,order-batch,order-common}/
        ├── investigator-b/{order-web,order-batch,order-common}/
        ├── investigator-c/{order-web,order-batch,order-common}/
        └── outputs/{a,b,c,reconciler}/
```

各リポジトリを横断する入出力・制約の取り決め、移行順序、互換構成、E2Eシナリオは `*-system-ops` が所有する。
アプリ内のテスト、Dockerfile、DB migrationなどの実装は該当アプリrepoが所有する。system-opsはそのSHAと、実装が満たす入出力・制約の取り決めを参照する。
共通ライブラリはComponentとして扱う。配布JARは各アプリ成果物に組み込まれるため、Deploymentには各アプリの組み込み版も記録する。

## Gitに置く内容
要約、構造化された承認済み知識、ADR、タスク、シナリオ、マニフェスト、証跡の保存先とダイジェストをGit管理する。
大量ログ、DBデータ、実画面、秘密情報はアクセス制御した証跡ストアへ保存し、保持期限とマスキング条件を定める。
`.gitignore` は補助であり、出力時の秘密情報除去とレビューを主な保護に使う。

## checkoutの扱い
MVPはURLとSHAを持つlockから独立cloneまたは読み取りSnapshotを作る。
Git submoduleを必須にせず、各アプリrepoの履歴と権限を独立して扱う。
worktreeを使う場合もGitメタデータや兄弟出力にアクセスできる可能性を考慮し、プロセス・ファイルアクセス制御で隔離を実装する。
大規模システムは全repoを3回全文読ませるだけでなく、重要な入出力・制約の取り決めを全員が確認し、詳細調査をrepo単位に並列化する。

## 別システムとも共通のrepo
共有Componentにグローバルな識別子と所有者を付ける。各システムは使用版を自身のlockに固定する。
更新通知は各システムの影響分析Taskへ渡し、承認とリリースは各境界で行う。
