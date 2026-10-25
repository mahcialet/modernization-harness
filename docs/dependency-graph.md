# システム依存グラフ

## ノードと方向
ノードはApplication、Component、Resource、外部Serviceであり、Repositoryは所有元への参照である。
基本方向は **consumer → provider** とする。
同じ二者間でもライブラリ利用、HTTP通信、テーブル更新などを別edgeにする。
各edgeには、依存先を利用するための入出力・制約・実行条件を記録する。以下では、これらの取り決めを契約と呼ぶ。

| 種類 | 記録する契約 |
|---|---|
| build-library | Maven等の座標、実JAR hash、ソースSHA、Java target、API/ABI |
| runtime-api | URL/経路、入力出力、認証、timeout、retry、エラー契約 |
| shared-db-read / shared-db-write | 接続先、schema/table、列・view・procedure、分離レベル、ロック |
| event-produce / event-consume | channel、schema、順序、重複排除、再配信 |
| file-produce / file-consume | 形式、文字コード、改行、配置、確定・回収タイミング |
| batch-order | 起動元、完了条件、排他、リトライ、スケジュール |
| configuration | JNDI、環境変数、認証・セッション・共有設定 |

宣言・バイナリ・実観測を区別し、未確認edgeも確度と追加調査方法付きで残す。
共有DBは `Web→DB` だけで終えず、テーブルのread/write集合と不変条件まで掘り下げる。

## 循環と移行単位
実システムには循環があり得るため、依存グラフ自体は有向グラフとして保持する。
強連結成分を使って協調変更が必要な候補を抽出し、bridgeや後方互換契約によって分割できるか判断する。
作業のTask DAGは別物であり、循環を検出したらタスク分解・前提条件を修正する。

## 影響解析
変更ノードからconsumer方向へ逆到達し、契約・環境・版で絞って再検証候補を得る。
共有DBのwriter変更はreaderとwriterの双方を対象候補にする。
所有者不明、動的URL、反射、生成コードなどで根拠が不足する場合は追加調査と広めの回帰検証を設定する。

## 互換構成
全組合せではなく、実際の切替経路と復旧経路に存在する組合せを列挙する。
旧Web＋新Batch、旧Batch＋新DB schema等を、境界契約ごとに検証する。
共通JARは実行中の独立サービスではなく、Web/Batchそれぞれに組み込まれたバージョンとして比較する。
