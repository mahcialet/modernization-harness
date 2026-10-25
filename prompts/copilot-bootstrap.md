# Copilot CLIへの初回依頼

このリポジトリの `README.md`、`AGENTS.md`、`IMPLEMENTATION_STATUS.md`、
`docs/architecture.md`、`docs/data-contracts.md`、`docs/template-versioning.md`、
`docs/execplans/EP-000-bootstrap.md` を読んで、EP-000で定めるデータ形式・必須項目・参照関係の定義、その検証、fixtureを実装してください。

目的は、複数repoをシステム単位で調査・照合し、その結果を移行計画・比較検証・継続保守へつなぐことです。
この配布物にはテンプレート操作の参考実装があります。先にテストし、使える部分を維持して不足を補ってください。
実行エンジンの言語・永続化方式は、配布性、クロスプラットフォーム性、保守性、既存コードを評価してADRに記録してください。

初回は固定Snapshot、安定ID、JSON Schema、参照整合性、Run/Attempt、承認digestを中心に作業してください。
将来のTask/Scenarioのデータ定義とProviderの操作・能力・権限の取り決めは保持し、実EC2接続や対象アプリの変更は対応する後続EPで実装します。
小さなPRへ分割し、実施内容、理由、テスト結果、未検証範囲、次の作業を日本語で記録してください。
Copilot CLIの実行機能は実際の導入版で確認し、未確認のCLI optionを前提に設計しないでください。
