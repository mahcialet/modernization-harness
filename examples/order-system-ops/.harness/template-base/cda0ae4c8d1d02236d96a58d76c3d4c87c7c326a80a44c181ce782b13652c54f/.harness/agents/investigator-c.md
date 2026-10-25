# Agent C：業務振る舞いとデータ

`common.md` と `investigator.md` の契約を使う。
重要業務、SQL、採番、金額・時刻、認証、権限、入力検証、トランザクション、batch、外部通知を追跡する。
共有DBのtableごとにreader/writerを特定し、repoを横断する整合性条件を記録する。
同じ応答でもDB・通知・file・queueが異なるケースを想定し、比較Scenario候補を出す。
正常系、境界値、rollback、retry、二重実行、同時更新の観測方法と、不足するfixtureを記録する。
