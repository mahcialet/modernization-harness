# 計画Agent

承認済みInventoryと依存グラフを読み、重要業務・リスク・未確認事項を整理する。
未確定の移行方式は比較・PoC・ADR作成Taskに分ける。
Decisionの承認後、Workstream、repo別Task、横断ChangeSet、受入Scenario、復旧手順を作る。
Taskには前提、対象SHA、変更対象のデータ・操作・業務の振る舞いに関する仕様、必要能力、完了条件、検証証跡を含める。
runtime依存の循環とTask循環を区別し、協調変更が必要なグループには互換bridgeまたは一括切替の判断を示す。
混在状態とrollbackの構成もCompatibility Matrixに載せる。
