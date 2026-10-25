# システム管理のAgent指示

`.harness/AGENTS.template.md` の共通方針と `AGENTS.project.md` の個別条件を読み、両方を今回のscopeへ適用する。
不一致がある場合は、現在の承認Decisionと個別条件を確認し、必要な判断を記録してから作業する。
文書は日本語で、実施したこと、次に行うこと、その理由を記述する。
初期の対象アプリ作業は現状調査とする。移行実装は承認InventoryとDecisionから作ったTaskで開始する。
テンプレート更新は `.harness/template.lock.json` に基づく差分レビューで行う。
