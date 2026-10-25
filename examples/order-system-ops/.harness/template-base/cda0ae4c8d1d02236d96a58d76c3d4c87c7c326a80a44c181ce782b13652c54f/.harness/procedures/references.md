> 配布元の設計書の参照コピー。本文中の `docs/`、`tools/`、`schemas/`、`templates/` は、配布元 `modernization-harness` を基準とする。

# 外部仕様の参照

確認日：2026-10-25。実装開始時には導入環境の版と公式資料を再確認する。

## R1：GitHubのリポジトリテンプレート

生成されたリポジトリの履歴とforkの違い。

`https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template`

## R2：Gitの三者ファイルマージ

current、base、otherによる差分統合。

`https://git-scm.com/docs/git-merge-file`

## R3：Copilot CLIのカスタム指示

AGENTS.md、.github/copilot-instructions.md、追加ディレクトリの発見。

`https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions`

## R4：Composeのproject名

project名による環境の識別と分離。

`https://docs.docker.com/compose/how-tos/project-name/`

## R5：AWS Systems Managerのセッション開始

接続前提、port forwarding、ログの制約。

`https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html`

## R6：JSON Schema Draft 2020-12

同梱スキーマの仕様。

`https://json-schema.org/draft/2020-12`

## R7：コンテナとカーネル

コンテナとVMの実行条件の違い。

`https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/`
