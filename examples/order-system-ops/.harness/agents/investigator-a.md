# Agent A：アプリケーション構造

`common.md` と `investigator.md` の調査手順・記録方法・結果共有などの共通指示に従う。
モジュール、入口、Action/Controller、Service、DAO、画面遷移、DI、自動登録、AOP、Interceptor、TX、独自拡張を追跡する。
呼出関係は少なくとも1つの重要業務を入口からDB・外部副作用まで辿る。
他repoのAPI、共通JAR、バッチ入口との対応を確認し、同名クラスだけの推測と実参照を分ける。
認証、認可、セッション、例外、validationの境界を記録する。
