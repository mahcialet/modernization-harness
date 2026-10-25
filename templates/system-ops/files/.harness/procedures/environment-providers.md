> 配布元の設計書の参照コピー。本文中の `docs/`、`tools/`、`schemas/`、`templates/` は、配布元 `modernization-harness` を基準とする。

# 環境Providerとコンテナ再現

## 共通契約
すべてのProviderについて、提供する操作、必要な能力、実行権限の確認方法を定める。
Providerは `describe / acquire / connect / health / observe / execute / reset / release` を能力付きで公開する。
「環境の能力」と「今回与えた権限」と「シナリオが要求する能力」を別々に持ち、実行前に交差を検査する。
許可されていない操作は `blocked` として必要承認と代替検証を返す。
外部接続先は接続時に識別し、account、region、instance、endpoint、deploy digestを記録する。

| Provider | 初期用途 | 状態を変える操作 |
|---|---|---|
| compose | 新旧システムの独立再現 | 自分のleaseに属する初期化・シナリオ実行 |
| ec2-observe | 配置・稼働・設定の観測 | 承認した観測処理の副作用範囲 |
| ec2-sandbox | 検証用EC2と隔離DB | 復元・障害注入・writeを承認計画内で実施 |
| agent-env | 将来の外部環境管理連携 | 同じ能力・権限の取り決めを満たす操作 |

## Composeの構成
1回の比較には、新旧それぞれ別project名、ネットワーク、DB volume、queue、ファイル領域、外部stubを使う。
Composeのproject名は環境分離に利用できる。[R4]
共有の固定 `container_name`、外部volume名、固定host portがある場合は分離条件を別途確認する。
データの論理内容は共通fixtureから作り、実volumeは共有しない。
外部stubは片側ずつ別インスタンスにし、録画した送信履歴を比較する。

## 再現度
コンテナではユーザー空間を再現し、コンテナ間で共有されるOSカーネル、起動サービス、EC2固有条件は実環境検証の対象として分ける。[R7]
AL1/AL2、旧JDK、Tomcatの実際の版・配布物は調査から固定し、出所とhashを記録する。
古い依存物は隔離された検証用の取得・保存経路で扱い、実運用の秘密情報は使わない。

## ライフサイクル
lease IDと所有リソースの一覧を記録し、準備→初期化→観測→証跡確定→回収を進める。
クラッシュ後もlease記録から所有リソースを確認して回収できるようにする。
初期化前後の検査、readiness、外部送信抑止、並列実行の干渉検査をProviderの受入条件にする。
