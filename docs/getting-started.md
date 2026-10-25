# 展開して使い始める

## 1. 配布元を置く
ZIPを展開すると `modernization-harness/` ができる。このディレクトリを配布元Gitリポジトリとして管理する。
以下は配布元ディレクトリで実行する。Python 3.11以上を使う。Windowsでは環境に合わせて `python3` を `py -3` に読み替える。

```bash
python3 tools/check_bundle.py
python3 -m unittest discover -s tests -p test_templates.py -v
```

ファイルの配布時checksumを確認してから、必要に応じて `git init`、レビュー、commit、タグ付けを行う。
バージョン0.1.0を最初の正式な配布版とし、GitHubのタグ作成や公開はまだ行っていない。
このZIPをGitHubのテンプレートリポジトリとして公開する場合も、システムごとの生成には `templates/system-ops` を使う。

## 2. システム管理リポジトリを生成する

実行前に、valuesのsystem_idとsystem_nameを自分のシステム名に変える。
生成先は新規または空のディレクトリを指定する。

```bash
python3 tools/template.py init --template templates/system-ops --values examples/order-system.values.json --destination ../order-system-ops
python3 tools/template.py status --target ../order-system-ops
```

このコマンドはGitの初期化・リモート作成・アプリcloneを実行しない。
生成先を独立したGitリポジトリにし、AGENTS.project.md、system.yaml、repositories.lock.yamlを調査して具体化する。
同梱の `examples/order-system-ops/` はこの操作で生成した架空例である。

## 3. アプリ側の追加候補を生成する

```bash
python3 tools/template.py init --template templates/application-overlay --values examples/application.values.json --destination ../app-overlay-review
```

出力のAGENTS.modernization.md、.modernization/system-link.json、docs/modernization/README.mdを既存アプリの規約と比較し、必要な内容をPRで取り込む。
この一時領域のlockと基準は生成内容の確認用であり、既存アプリへそのまま全コピーする運用とは分ける。

## 4. 契約と全テストを検証する
ここでは、データに定めた形式・参照関係の検査と、全テストを実行する。
外部依存の取得が許可された開発環境で実行する。テンプレート生成にはこの追加依存は不要である。

```bash
python3 -m venv .venv
# Linux/macOS:
. .venv/bin/activate
# Windows PowerShellでは .venv\Scripts\Activate.ps1 を使う。
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python tools/validate.py examples/contracts/fixture-system.json
```

fixtureは構造・参照の検査例であり、実アプリの調査結果ではない。
`--ready` は架空例や未解決のrepo/SHAを検出する追加検査であり、実環境の安全性や接続権限までは判定しない。

## 5. 新しいテンプレート版を取り込む
新リリースを `../modernization-harness-next` に展開した例を示す。
導入先は更新専用ブランチで作業し、同時に別の処理が書き換えない状態を用意する。

```bash
python3 tools/template.py plan --target ../order-system-ops --template ../modernization-harness-next/templates/system-ops --output ../template-review-next
```

`review.md`、`upstream.diff`、`incoming/`を確認する。導入先にはまだ変更が入らない。
競合がある場合は、採用したい結果を指定する。

```bash
python3 tools/template.py resolve --plan ../template-review-next --path AGENTS.md --choice keep-local
# または採用する統合ファイルを作って指定する。
# python3 tools/template.py resolve --plan ../template-review-next --path AGENTS.md --choice file --file ../reviewed-AGENTS.md
```

解決後の `plan.sha256` にある64桁を確認し、以下のPLACEHOLDERをその値へ置き換える。

```bash
python3 tools/template.py apply --plan ../template-review-next --approve PLACEHOLDER
```

計画後の変更やpayload改変を検出すると適用を中止する。新しい計画を作って再レビューする。
適用後はGit差分とテストを確認し、共通ファイル、lock、新基準を同じPRに含める。
seedの提案は参考として表示され、既存の個別設定は維持される。必要なseed変更は別のレビュー差分で行う。
レビュー出力には導入先の現行内容を含む場合があるため、対象リポジトリと同等のアクセス制御で保管する。

## 6. Copilotへ引き継ぐ
ハーネス開発は `prompts/copilot-bootstrap.md` を使う。
実システムの現状調査はsystem-opsの `.harness/prompts/investigate-only.md` を使い、repo群の完全SHAと調査権限を確定して開始する。
