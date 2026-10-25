# 元資料と更新内容

## bootstrap資料からの拡充

元ファイル：`modernization-harness-bootstrap.zip`
SHA-256：`f37bc05a08fdd2a910193f7d1adb8e3580bf7868fa777d1c445ff6eead21dacb`

元ZIPの8ファイルを確認した上で、本配布物を作成した。新しい実システムの調査結果は含めていない。

| 旧ファイル | 今回の扱い |
|---|---|
| AGENTS.md | 日本語・肯定形の行動指針を継承し、システム管理とテンプレート版管理を追加 |
| README.md | 配布物の入口、現時点の機能、初期化手順を再構成 |
| agents/investigator.md | 共通の調査項目・出力形式とA/B/Cの役割を具体化 |
| agents/reconciler.md | 横断照合、未解決、根拠判定を具体化 |
| docs/architecture.md | 日本語へ統一し、構成・状態・環境の責務を明示 |
| docs/execplans/EP-000-bootstrap.md | 完了条件を具体化し、後続EPへ分割 |
| schemas/claim.schema.json | 0.1.0のスコープ・Snapshot参照を含むデータ定義へ更新 |
| workflows/investigate.yaml | 複数repo・独立性・失敗時の合流条件を定義 |

正式なGitタグ、GitHubリポジトリ、AWSリソースはこの作業では作成していない。

## 初回リリースの版番号確定

版番号確定の直接の元資料は、作成途中に仮の版番号を付けた `modernization-harness-all-in-one-v0.2.0.zip`。
SHA-256：`e9340c94907e437e6861ca6ba0b0ac004ec1399cc124edf751bca8cc7e6a73a3`。
元ZIPの配布ファイル276件について同梱チェックサムの一致を確認した。

2026-10-25の決定により、この一式を最初の正式な配布版 **0.1.0** として整理した。
旧草案の0.2.0は正式リリース履歴には数えない。
VERSION、テンプレートのmanifest、リリースタグ規約、初期スキーマ、サンプル、ワークフロー、更新計画の版表記を揃えた。
生成例は新しいテンプレートから再生成し、lock、template-baseのディレクトリ名と内容ハッシュ、配布チェックサムを計算し直した。
更新テストでは検査専用の0.1.1を使い、旧版拒否のケースには検査専用の0.0.9を使う。これらはリリース済みの版を意味しない。
機能の追加や移行先技術の決定は今回の変更に含めていない。
