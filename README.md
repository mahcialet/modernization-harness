# Modernization Harness：設計・テンプレート一式

複数リポジトリの独立調査から、モダナイゼーション、その後の継続保守までを扱うハーネスの開発キット。
**初回リリース：0.1.0。オーケストレーター本体はこれから実装する。**

この一式を正式な版管理の起点とする。リリース履歴は `CHANGELOG.md`、作成途中の資料の来歴は `docs/source-update-log.md` に記録する。

## 管理する3層

| 層 | 例 | 責務 |
|---|---|---|
| 配布元 | `modernization-harness` | 汎用ハーネス、スキーマ、Agent指示、版管理するテンプレート |
| システム管理 | `order-system-ops` | システム定義、複数repoのSHA固定、調査、ADR、計画、新旧比較の条件と判定基準、保守 |
| アプリケーション | `order-web` / `order-batch` / `order-common` | 実装、アプリ固有テスト、ビルド成果物 |

既存アプリケーションのGit履歴は維持する。実行用clone/worktreeは各管理リポジトリの外に配置する。

## 含む設計
独立調査3Agent＋照合1Agent、証拠からタスクまでの追跡、システム依存グラフ、タスクDAG、
新旧・混在構成の比較、コンテナ再現、実EC2観測と隔離検証、承認と証跡、継続保守、テンプレート更新。
移行先Javaフレームワーク・JDK・OSの具体的な版は、実システムの調査後に選定する。

## すぐに使えるもの
- 日本語の設計書、ExecPlan、Agent指示、Seasar2調査プロファイル。
- システム管理リポジトリとアプリ連携ファイルのテンプレート。
- JSON Schema、構造化データのサンプル、検証用フィクスチャ。
- ローカル専用のテンプレート初期化・更新計画・承認適用ツールとテスト。

自動Agent起動、アプリ比較エンジン、AWS接続、デプロイ、定期実行は設計段階である。
実装状況は `IMPLEMENTATION_STATUS.md` を参照する。

## 最初の操作
以下はこのディレクトリをカレントにして実行する。Python 3.11以上を使う。

```bash
python3 tools/template.py init --template templates/system-ops --values examples/order-system.values.json --destination ../order-system-ops
python3 tools/template.py status --target ../order-system-ops
python3 -m unittest discover -s tests -p test_templates.py -v
```

テンプレートツールとそのテストはPython標準ライブラリだけで動く。全テストと、構造化データの形式・参照・タスクDAGの検証には `requirements-dev.txt` の依存が必要である。

初期化したディレクトリは独立Gitリポジトリとして管理する。GitHubへの登録、Gitの初期化、タグ作成はツールから自動実行しない。
`system.yaml`、`repositories.lock.yaml`、環境定義の未確定値を調査で埋める。
`examples/order-system-ops/` は生成済みの架空例であり、本番情報を含まない。

## テンプレート版管理
配布元を `template-v0.1.0` のようなタグでリリースし、導入先の `.harness/template.lock.json` で版・配布内容・適用基準を追跡する。
このZIPにはローカル配布内容のダイジェストが入っている。GitHubのタグやリリースはまだ作成していない。
更新時は旧配布基準・導入先・新配布内容を比較し、レビューした計画だけを適用する。
テンプレート版、データスキーマ版、将来の実行エンジン版、対象システムの版は別々に管理する。

## 読み始める順序
1. `docs/getting-started.md`：展開後の手順。
2. `docs/repository-layout.md` と `docs/template-versioning.md`：配置と更新方式。
3. `docs/architecture.md` と `docs/data-contracts.md`：各構成要素の責務と、受け渡すデータの形式・必須項目・参照関係。
4. `docs/execplans/EP-000-bootstrap.md`：初回実装範囲。
5. `CHATGPT_HANDOFF.md` と `prompts/copilot-bootstrap.md`：Copilotへの引継ぎ。

全体の検証結果は `QUALITY_REPORT.md`、ファイル整合性は `PACKAGE_CONTENTS.sha256` に記録する。
