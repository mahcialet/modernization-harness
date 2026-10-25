# データ契約

ここでは、記録するデータの必須項目・型・参照関係と、改訂・承認の扱いを定める。これらをデータ契約と呼ぶ。

## 安定IDと改訂
IDはSystemに属する名前空間付きの文字列とする。例：`FD-order-system-transaction-001`。
同じ事実の改訂は `revision` と `supersedes` で追跡し、Runの過去出力は不変に保持する。
物理ファイルの移動に依存せず、IDとcontent digestから参照を解決する。
テンプレートのschema版は0.1.0。データ移行は新しい成果物を作り、元の記録と対応付ける。

| 型 | 必須の意味 | 主な参照 |
|---|---|---|
| System | repo・アプリ・ライブラリ・共有資源の所属 | Repository / Application / Component / Resource |
| RepositoryLock | 完全SHA、追跡元ref、解決時刻 | System |
| Snapshot | 検証対象のソース・成果物・設定・初期状態 | Lock / Environment / artifact digest |
| Run | 入力Snapshot、役割、能力、状態、Attempt | Snapshot / prompt digest |
| Evidence | 根拠の所在、観測時点、内容hash、秘匿区分 | Snapshot / repository / artifact |
| Claim | Agentの主張、対象、確度、根拠 | Run / Evidence |
| Finding | 照合された主張、判定、未解決の影響 | Claim / Evidence |
| Dependency | consumer→provider、種類、入出力・制約・実行条件の取り決め、環境、確度 | Entity / Evidence |
| Inventory | 採用Finding一覧、Coverage、未解決 | Snapshot / Finding |
| Decision | 判断、理由、適用範囲、状態 | Finding / Approval |
| Task | 成果、対象repo、依存、前提、検証、復旧 | Finding / Decision / Task |
| Scenario | 入力列、初期状態、観測、必要能力、副作用 | Finding / Contract |
| Observation | 新旧それぞれの生観測と正規化版 | Scenario / Snapshot / Evidence |
| Comparison | 一致・意図差・回帰・判定不能、観測範囲 | Observation / AcceptedDifference |
| AcceptedDifference | 厳密な差分条件、理由、期限、承認 | Decision / Scenario / Approval |
| Deployment | 実環境で観測した成果物・配置 | Environment / artifact / observation time |
| Approval | 人の判断と対象digest、範囲、期限 | inventory / decision / plan / environment |

## 根拠の強さ
ソースに宣言があること、ビルド成果物に含まれること、実環境で利用されていることを区別する。
例えばpom.xmlのJDBC依存は「宣言」の根拠であり、稼働中のDataSourceの製品・版を確定するには配備物か観測根拠を追加する。
Evidenceは `source / artifact / runtime / external` の種類と `declared / packaged / observed` の観測層を持つ。

## 機械検証と意味の検証
スキーマは必須項目・型・列挙値を検査する。参照検査はID解決、重複、scope、snapshot一致、Task循環を検査する。
照合Agentは証拠が主張を本当に支えるかを判定し、人が重要事項を承認する。
形式検査だけで同等性・安全性・承認者の本人性まで確認できるとは扱わない。

## 承認と陳腐化
承認は成果物の正確なdigestに結び付ける。承認後の変更には新たな承認が必要となる。
根拠repoの変更、依存artifactの変更、環境差分は関連Findingを `stale` にし、影響するDecision・Task・Scenarioへ再評価要求を伝播する。
根拠との関連が不足する変更は保守的に影響範囲を広げる。再調査後も以前の承認済み記録は履歴として残す。
