# Seasar2 / Tomcat / Amazon Linux調査プロファイル

対象技術は調査開始時の仮説として扱い、実ファイル・バイナリ・実観測で確認する。

## 見る項目
S2Container、dicon、SMART deploy、自動登録、AOP、独自Interceptor、S2Tiger、S2Dao、S2JDBC、S2Struts、SAStruts、Teeda等の利用有無を確認する。
候補に名前があることを導入済みとは扱わず、利用箇所と版の根拠を記録する。
JSP、taglib、validation、型変換、例外、認証、session、JNDI、Realm、Connector、文字コード、locale、timezone、native library、cron、shellを確認する。
SQLの動的条件、DB方言、procedure、採番、楽観/悲観lock、auto-commit、手動commit、独自TX、別processの更新も追う。
Maven/Gradle/Ant、社内artifact、vendor JAR、web.xml、context.xml、JVM options、配備WAR/JARの情報を分けて記録する。

## 現段階の出口
現状Inventory、repo横断の境界、Unknown、追加観測計画、Characterization Scenario候補を作る。
JDK・OS・フレームワークの選定はこの情報をレビューした後に行い、最新サポート状況をその時点の公式情報で再確認する。
