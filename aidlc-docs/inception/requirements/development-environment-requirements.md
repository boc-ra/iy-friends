# Development Environment Requirements

## Intent Analysis

- **User request**: Gitによるバージョン管理、CI/CD、開発用Codex Skills、Codex Hooks、Git hooksを整備する。
- **Request type**: Development environment enhancement and delivery automation
- **Scope**: Workspace-wide monorepo configuration across public web, admin web, backend API, infrastructure, and development tooling
- **Complexity**: Moderate
- **Risk**: Medium。公開リポジトリ化と本番AWSへのデプロイ経路を含むため、情報公開と権限管理に注意が必要。

## Selected Direction

- GitHubの公開リポジトリを使用する。
- ワークスペース全体を単一monorepoとして管理する。
- PRと`main`へのpushで全コンポーネントのCIを実行する。
- 本番AWSへのCDは手動起動かつ承認付きとし、GitHub OIDCを使用する。
- 管理画面はCIで検証するが、本番へはデプロイしない。
- Codex HooksとGit pre-commit hooksの両方を整備する。

## Functional Requirements

### FR-DEV-01 Git Repository

- ワークスペースルートをGitリポジトリのルートにする。
- 既定ブランチを`main`にする。
- 4プロジェクト、共有ドキュメント、リポジトリ固有のSkillとHookを一括管理する。
- `node_modules`、`dist`、`.aws-sam`、Pythonキャッシュ、テストキャッシュ、仮想環境、`.env`、ローカル専用設定を追跡しない。
- 初回コミット前に秘密情報、個人情報、不要な生成物を検査する。

### FR-DEV-02 Continuous Integration

- Pull Requestと`main`へのpushをトリガーにする。
- 公開Webと管理Webで依存関係の再現可能なインストール、型検査、ビルドを実行する。
- バックエンドでpytestを実行し、既存のHypothesisテストを含める。
- バックエンドと共有インフラのSAMテンプレートに対してlint検証する。
- Pythonとnpmの依存関係監査を実行する。
- CIは管理画面をビルドするが、デプロイしない。

### FR-DEV-03 Continuous Deployment

- 本番デプロイはGitHub Actionsの手動起動に限定する。
- GitHub Environmentによる承認ゲートを使用する。
- AWS認証はGitHub OIDCを使用し、長期Access KeyをGitHub Secretsへ保存しない。
- デプロイ対象を明示的に選択できるようにする。
- 依存関係がある一括デプロイでは、共有インフラ、バックエンド、公開Webの順序を守る。
- 公開WebのデプロイはS3同期後にCloudFront invalidationを実行する。
- 管理WebはCD対象外とする。
- 本番変更は実行前に対象、ブランチ、コミットを表示する。

### FR-DEV-04 Repository Skill

- リポジトリ固有Skillを`.agents/skills`に配置する。
- Skillにはプロジェクト構成、検証コマンド、AWSデプロイ順序、本番操作の承認境界、生成物と秘密情報の扱いを記載する。
- 一般的な開発助言は重複させず、このプロジェクト固有の非自明な情報に限定する。
- Skillは通常の自動検出を許可する。

### FR-DEV-05 Codex Hooks

- `.codex/hooks.json`とリポジトリ内のHookスクリプトを使用する。
- セッション開始時にリポジトリ固有の重要なコンテキストを追加する。
- 本番AWS、破壊的Git操作、秘密情報を含むファイルへの操作を事前検査する。
- Hookは安全ガードとして扱い、AWS IAMやGitHub承認ゲートの代替にしない。
- Hookの拒否理由は開発者が理解できる形で返す。

### FR-DEV-06 Git Pre-commit Hooks

- ステージされたファイルだけを対象に高速検査する。
- `.env`、認証情報、秘密鍵、大きすぎる生成物のコミットを防止する。
- 空白・競合マーカー・基本的な構文問題を検出する。
- 重いビルドと全テストはCIへ委ね、通常のコミット操作を過度に遅くしない。

### FR-DEV-07 Developer Documentation

- ルートから各プロジェクトのセットアップ、検証、Git hooks有効化、CI/CD運用を確認できるようにする。
- Windowsローカル環境とGitHub ActionsのLinux環境の差異を明記する。
- Python 3.13がローカルに未導入である現状を明記する。

## Non-functional Requirements

### NFR-DEV-SEC Security

- 公開前に追跡候補ファイルを検査し、秘密情報や公開不要な個人情報を除去する。
- GitHub Actionsの権限はworkflow単位で最小化する。
- 外部Actionsは信頼できる提供元を使用し、可能な範囲で不変のコミットSHAへ固定する。
- OIDC Trust Policyは対象GitHubリポジトリ、ブランチ、Environmentへ限定する。
- 本番デプロイRoleは必要なCloudFormation、SAM成果物、S3、CloudFront操作だけに制限する。
- Fork由来のPull Requestへ本番Secretsやデプロイ権限を渡さない。

### NFR-DEV-COST Cost Control

- GitHub標準Linux runnerを使用する。
- 不要なArtifactを保存しない。
- GitHub Actionsの無料利用枠を前提とし、予算通知または超過停止を設定できる構成にする。

### NFR-DEV-REL Reliability

- CIの依存関係インストールはlock fileを使用する。
- 本番CDは同時実行を制御し、複数デプロイの競合を防止する。
- 失敗時は後続コンポーネントをデプロイしない。
- CloudFormation Change Set確認と既存の`confirm_changeset`方針を維持する。

### NFR-DEV-MAINT Maintainability

- CI/CDの共通処理を過度に複製しない。
- HookスクリプトはWindowsとGitHub Actionsで検証可能な実装にする。
- リポジトリ固有Skillと開発ドキュメントで同じ情報を重複管理しない。

### NFR-DEV-TEST Testability

- Hookスクリプトの許可・拒否判定を副作用から分離し、代表例でテスト可能にする。
- 既存のHypothesis PBTをCIで必ず実行し、shrinkingと再現情報を保持する。
- 新しい純粋な解析・正規化処理に識別可能な不変条件がある場合は、部分適用中のPBTルールに従う。

## Out of Scope

- 管理Webの本番ホスティング
- `main`へのpushだけで行う無承認の本番自動デプロイ
- アプリケーション機能や画面内容の変更
- 現時点でのAWS本番リソース削除
- GitHub有料プランやlarger runnerの導入

## Acceptance Criteria

- ルートGitリポジトリで意図したファイルだけが追跡候補になる。
- 公開前スキャンで重大な秘密情報が検出されない。
- CI定義が全対象コンポーネントを検証する。
- CD定義が手動起動、承認、OIDC、対象選択、同時実行制御を備える。
- 管理Webがデプロイ処理に含まれない。
- リポジトリSkillが公式の配置規則に従い、validatorを通過する。
- Codex Hooksが公式schemaに従い、安全な操作を許可し危険な代表操作を拒否する。
- Git pre-commit hooksが秘密情報と生成物の代表例を拒否する。
- ローカルで実行可能な検証が成功し、ローカルPython不足による未実行項目は明示される。

## Extension Compliance

- **Security Baseline**: Applicable and blocking。公開リポジトリ、サプライチェーン、OIDC、秘密情報、最小権限へ適用する。
- **Property-Based Testing**: Partial mode。既存HypothesisテストをCIへ含め、新規の純粋関数・シリアライズ処理へ該当ルールを適用する。
- **Resiliency Baseline**: Disabled。今回も適用しない。
