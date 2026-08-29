# Development Environment Requirements Questions

Git、CI/CD、Codex Skills、Hooks の初期構成を決めるための質問です。
各質問の `[Answer]:` に選択肢の文字を記入してください。

## Question 1
リポジトリの配置と公開範囲をどのようにしますか？

A) GitHub に非公開リポジトリを作成する（推奨）

B) GitHub に公開リポジトリを作成する

C) 当面はローカルGitのみ使用し、リモートは後で設定する

X) Other（`[Answer]:` の後に希望を記述）

[Answer]: B

## Question 2
現在の4プロジェクトをGit上でどのように管理しますか？

A) ワークスペース全体を1つのmonorepoとして管理する（推奨）

B) public-web、admin-web、backend-api、infraを別リポジトリに分割する

X) Other（`[Answer]:` の後に希望を記述）

[Answer]: A

## Question 3
CIで常時検証する範囲を選んでください。

A) PRとmainへのpushで、両フロントの型検査・ビルド、バックエンドテスト、SAM lint、依存関係監査を実行する（推奨）

B) 最初は型検査・ビルド・バックエンドテストだけ実行し、セキュリティ監査は後で追加する

C) バックエンドのみCI対象にする

X) Other（`[Answer]:` の後に希望を記述）

[Answer]: A

## Question 4
本番AWSへのCD方針を選んでください。

A) GitHub Actionsの手動承認付きworkflow_dispatchから、OIDCで本番デプロイする（推奨）

B) mainへのpushで本番へ自動デプロイする

C) まずCIだけ整備し、本番CDは後で追加する

X) Other（`[Answer]:` の後に希望を記述）

[Answer]: A

## Question 5
試作段階の管理画面をCI/CDでどう扱いますか？

A) CIでは型検査・ビルドするが、本番にはデプロイしない（推奨）

B) CI/CDの対象から除外する

C) 将来用の管理画面デプロイworkflowを無効状態で用意する

X) Other（`[Answer]:` の後に希望を記述）

[Answer]: A

## Question 6
Hooksをどこまで整備しますか？

A) Codex HooksとGit pre-commit hooksの両方を整備する（推奨）

B) Codex Hooksのみ整備する

C) Git pre-commit hooksのみ整備する

X) Other（`[Answer]:` の後に希望を記述）

[Answer]: A
