# AI-DLC State Tracking

## Project Information
- **Project Type**: Greenfield
- **Start Date**: 2026-07-19T13:36:32Z
- **Current Stage**: CONSTRUCTION — Development Environment Foundation complete
- **Current Unit**: —
- **Construction Unit Order**: U3 backend-api ✅ → U5 infra (current) → U4 blog-migration → U1 public-web (Phase 1); then U3(admin) → U5(auth) → U2 admin-web (Phase 2)

## Workspace State
- **Existing Code**: No
- **Programming Languages**: None detected
- **Build System**: None detected
- **Project Structure**: Empty (documentation-only workspace)
- **Reverse Engineering Needed**: No
- **Workspace Root**: C:\Users\syuto\IY FRIENDS

## Code Location Rules
- **Application Code**: Workspace root (NEVER in aidlc-docs/)
- **Documentation**: aidlc-docs/ only
- **Structure patterns**: See code-generation.md Critical Rules

## Execution Plan Summary
- **Stages to Execute**: Application Design, Units Generation, Functional Design, NFR Requirements, NFR Design, Infrastructure Design, Code Generation, Build and Test
- **Stages to Skip**: Reverse Engineering (Greenfield)
- **Release Strategy**: 2段階（Phase 1 公開サイト＋問い合わせ送信 / Phase 2 管理CMS）

## Stage Progress
### 🔵 INCEPTION PHASE
- [x] Workspace Detection
- [x] Reverse Engineering (SKIPPED — Greenfield)
- [x] Requirements Analysis
- [x] User Stories
- [x] Workflow Planning
- [x] Application Design
- [x] Units Generation

### 🟢 CONSTRUCTION PHASE (per-unit loop)
**Unit U3 backend-api (Phase 1) — ✅ COMPLETE**
- [x] Functional Design
- [x] NFR Requirements (Q-N1/N2/N3 = A/A/A 最低コスト構成)
- [x] NFR Design (Q-D1/D2/D3 = A/A/A 同期送信・軽量冪等・CDN/APIGWキャッシュ)
- [x] Infrastructure Design (Q-I1/I2/I3/I4 = A/A/A/A SAM・マルチテーブル・SSM・prod単独)
- [x] Code Generation (Phase 1: iyf-backend-api/ 生成、24 tests pass, PBTが clamp_limit のバグ検出→修正)

**Unit U5 infra (Phase 1) — 🔵 IN PROGRESS (stage assessment)**
- [x] Functional Design — SKIPPED (infra unit, no domain logic)
- [x] NFR Requirements — SKIPPED (folded into Infra Design; NFRs determined in requirements+U3)
- [x] NFR Design — SKIPPED (folded into Infra Design)
- [x] Infrastructure Design (Q-U1..U5 = A; SAM統一/共有インフラのみ・デフォルトドメイン・標準ヘッダ・最小監視・Phase1 Cognito)
- [x] Code Generation (IaC): iyf-infra/ SAM 生成・YAML検証PASS（14リソース/4 Outputs）

**Unit U5 infra (Phase 1) — ✅ COMPLETE**

**Unit U4 blog-migration (Phase 1) — 🔵 IN PROGRESS**
- [x] Functional Design — SKIPPED (methods/mapping defined in Application Design)
- [x] NFR Requirements — SKIPPED (one-time low-volume batch)
- [x] NFR Design — SKIPPED
- [x] Infrastructure Design — SKIPPED (no new AWS resources; imports to U3 Posts)
- [x] Code Generation (iyf-backend-api/migration/ 生成、33 tests pass, source_url冪等)

**Unit U4 blog-migration (Phase 1) — ✅ COMPLETE**

**Unit U1 public-web (Phase 1) — ✅ COMPLETE**
- [x] Functional Design — folded into Code Gen (page/component inventory)
- [x] NFR Requirements / NFR Design / Infrastructure Design — SKIPPED (UX NFRs determined; deploys to U5)
- [x] Code Generation — iyf-public-web/ (Vite+React+TS, apple-design, 9 pages, dummy-data local preview)

**🟢 Phase 1 ALL units complete: U3 ✅ / U5 ✅ / U4 ✅ / U1 ✅**

**Phase 2 (管理CMS) — unit order: U3 backend-api(admin) → U5 infra(auth/Cognito) → U2 admin-web**
Scope: US-07(ブログ投稿) / US-09(お知らせ投稿) / US-11(カレンダー登録) / US-14(問い合わせ管理) / US-15(ログイン・MFA) / US-16(編集者招待) / US-18(セキュリティ該当分)

**Unit U3 backend-api (Phase 2) — 🔵 IN PROGRESS**
- [x] Functional Design (auth: 認可matrix/IDOR/invite Cognito AdminCreateUser/displayName初回設定/draft±publish/監査CWL) — APPROVED (Q1A/Q2A/Q3B/Q4A/Q5B/Q6A/Q7A/Q8A)
- [x] NFR Requirements (N1A MFA=Admin必須TOTP/Editor任意, N2A TOTP, N3A token1h/1h/30d, N4A APIGW+Cognito) — defaults applied (empty tags), awaiting approval
- [x] NFR Design (二層認可/MFA/token patterns, GSI-status追加, Cognito隔離retry, listUsers=Scan≤10, email一意性=Cognito) — no new Q, awaiting approval
- [x] Infrastructure Design (単一HttpApi+ルート単位JWT authorizer, AdminFunction, ImportValue Cognito, GSI-status×3[Posts/Notices/Inquiries], cognito-idp IAM UserPool限定, backfill; shared-infra §3b 追記) — no new Q, awaiting approval
- [x] Code Generation — Part 1(plan承認) + Part 2(27 steps 全実装): auth module/handlers.admin(23routes)/各service管理メソッド/template.yaml(GSI-status×4+AdminFunction+JWT authorizer)/backfill/5 test files/docs。**pytest 79 passed**、全ソース py_compile OK。sam validate は Build&Test へ（SAM CLI無し）— awaiting approval

**Unit U3 backend-api (Phase 2) — ✅ COMPLETE**（FD/NFR-Req/NFR-Design/Infra/Code 全承認、pytest 79 passed）

**Unit U5 infra (Phase 2) — ✅ COMPLETE**
- [x] Functional/NFR/NFR-Design — SKIPPED (infra unit; folded)
- [x] Infrastructure Design (U5-1=A admin-web MFA強制/token 1h-1h-30d明示/初期admin runbook)
- [x] Code Generation (iyf-infra template: UserPoolClient token有効期限明示; Export不変=U3 Import維持; README bootstrap runbook)

**Unit U2 admin-web (Phase 2) — ✅ COMPLETE**
- [x] Functional Design (frontend-components) — APPROVED (U2-1A Amplify v6/U2-2A TipTap/U2-3A dummy)
- [x] NFR Requirements / NFR Design / Infrastructure Design — FOLDED/SKIPPED (frontend deploys to U5; UX NFRs確定)
- [x] Code Generation — Part1(plan承認)+Part2(16 steps): iyf-admin-web (Vite+React18+TS, 34 src files, Amplify auth+admin MFA強制, TipTap allowlist, dummy mode)。**tsc clean + npm run build 成功(708 modules)**

**🟢 Phase 2 ALL units complete: U3 ✅ / U5 ✅ / U2 ✅**

**Build and Test (Phase 2) — ✅ COMPLETE**（instructions: build/unit/integration/security/summary -phase2。backend pytest 79 passed、admin-web tsc+build pass）— awaiting approval → Operations

**After all units:**
- [x] Build and Test (Phase 1) — instructions generated (build/unit/integration/performance/security/summary); backend pytest 33 passed

### 🟡 OPERATIONS PHASE
- [x] Operations — runbook.md に Phase 2 デプロイ手順（Path D）追記（プレースホルダのため runbook で代替）

## Extension Configuration
| Extension | Enabled | Mode | Decided At |
|---|---|---|---|
| Security Baseline | Yes | Full (blocking) | Requirements Analysis |
| Resiliency Baseline | No | — | Requirements Analysis |
| Property-Based Testing | Yes | Partial (pure functions + serialization round-trips only) | Requirements Analysis |

## Change Request: Development Environment Foundation

- **Started**: 2026-08-29T12:21:56Z
- **Scope**: Root Git repository, public GitHub monorepo, CI/CD, repository Codex Skill, Codex Hooks, Git pre-commit hooks
- **Requirements Questions**: Completed (B/A/A/A/A/A)
- **Requirements Document**: `aidlc-docs/inception/requirements/development-environment-requirements.md`
- **Status**: U6 and U7 complete; public GitHub CI, protected main, approved production Environment, AWS OIDC bootstrap, and verification-only role assumption all verified
- **Execution Plan**: `aidlc-docs/inception/plans/development-environment-execution-plan.md`
