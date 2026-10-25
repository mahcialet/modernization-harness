# 新旧コンテナ環境

compose.yamlは起動前に実対象へ合わせる構成雛形である。healthcheck、JNDI/DB資格情報、起動command、seed方法を調査から具体化する。
旧・新を別project名で起動し、それぞれのDB volumeとstubを使う。環境ファイルでイメージdigest集合を切り替える。
外部ポートの公開は必要な観測経路に限定する。内部networkの指定に加え、host mount・権限・接続先・外部送信を検査する。
APP_DB_HOST等は説明用の変数名であり、実アプリの設定方式に合わせて更新する。
Composeおよび実アプリの起動は、このテンプレート配布時点では検証していない。
