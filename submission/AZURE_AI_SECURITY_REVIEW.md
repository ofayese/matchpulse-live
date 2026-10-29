# Foundry account and project — bounded security review

**Review date:** 2026-10-26  
**Attribution:** `UNEXPECTED_AI_ACCOUNT_ATTRIBUTION=USER_AUTHORIZED_VIA_VSCODE_FOUNDRY_EXTENSION`  
**Key activity:** `KEY_LIST_ACTIVITY_CONCLUSION=KEY_LIST_ACTIVITY_ATTRIBUTED_EXPECTED_TOOLING`  
**Inventory:** `AZURE_RESOURCE_COUNT_CURRENT=7`; five MatchPulse application/monitoring resources plus two separately authorized Foundry development resources.  
**Runtime:** `MATCHPULSE_RUNTIME_DEPENDENCY=NO`  
**Recommendation:** `AZURE_REMEDIATION_RECOMMENDATION=RETAIN_PENDING_POST_SUBMISSION_REVIEW`

This is a read-only review. The user confirmed that the account and project
were deliberately created through the Visual Studio Code Microsoft Foundry
extension toolkit. No resource was changed or deleted; no keys, tokens,
connection strings, OAuth material, or full identity claims were retrieved
or recorded. The two Foundry resources are not part of the submitted
MatchPulse runtime and are not deployed by MatchPulse Bicep.

## Attribution and Activity Log

A fresh 72-hour Activity Log read returned 88 events for the account. It
contained 32 successful `List Keys` operations, each paired with a `Started`
event under the same correlation, plus 18 `Write connections` events (nine
start/success pairs). Account/project creation, those connection writes, and
all 32 key-list operations had the same Activity Log caller field. Its
one-way pseudonym (`actor-A`) matches the account/project ARM creator field;
the account and project ARM records identify the creator type as `User`.
The creation and connection writes occurred in the same short session as the
first key-list calls, and subsequent successful key-list calls recur at
roughly 15-minute intervals. This is consistent with the user's stated
Foundry extension/toolkit activity.

The Activity Log response did **not** return the caller object ID, an
application/client ID, client/user-agent identifier, or an explicit
interactive/automated classification. The correlation IDs below are
one-way pseudonyms, not raw IDs. No non-key-list operation shared the
correlation IDs; each correlation contained only its `Started` and
`Succeeded` records. The project/connection writes were nearby in time and
used the same caller field, but were not correlated operations. This is
adequate for the requested expected-tooling attribution when combined with
the user's confirmation; it does not independently identify the VS Code
extension by application ID or user-agent. No keys were retrieved by this
review.

| Started UTC | Succeeded UTC | Sanitized correlation |
|---|---|---|
| 2026-10-26T14:29:36.623552Z | 2026-10-26T14:29:36.6859847Z | `corr-02a59ba656` |
| 2026-10-26T14:37:56.578028Z | 2026-10-26T14:37:56.6249029Z | `corr-a7237873b4` |
| 2026-10-26T14:52:38.5657765Z | 2026-10-26T14:52:38.6439024Z | `corr-2628d11799` |
| 2026-10-26T15:02:36.5841644Z | 2026-10-26T15:02:36.7872879Z | `corr-5cb17386cb` |
| 2026-10-26T15:17:31.6878644Z | 2026-10-26T15:17:31.7816105Z | `corr-59038ef518` |
| 2026-10-26T15:32:13.7530852Z | 2026-10-26T15:32:13.8155879Z | `corr-1b82adb6f6` |
| 2026-10-26T15:35:22.6121253Z | 2026-10-26T15:35:22.768365Z | `corr-98b08fe297` |
| 2026-10-26T15:50:03.3538326Z | 2026-10-26T15:50:03.4475829Z | `corr-dcd1c0f7f3` |
| 2026-10-26T16:04:46.4769353Z | 2026-10-26T16:04:46.5550566Z | `corr-19051d2a5b` |
| 2026-10-26T16:13:06.6714785Z | 2026-10-26T16:13:06.8433513Z | `corr-edd8fd27c5` |
| 2026-10-26T16:27:52.0503051Z | 2026-10-26T16:27:52.1128054Z | `corr-b674a020ca` |
| 2026-10-26T16:42:41.1271857Z | 2026-10-26T16:42:41.1896927Z | `corr-7ef860c5b4` |
| 2026-10-26T16:57:28.2985567Z | 2026-10-26T16:57:28.4391794Z | `corr-f04135789a` |
| 2026-10-26T17:12:22.4115641Z | 2026-10-26T17:12:22.4896953Z | `corr-fa586729d0` |
| 2026-10-26T17:27:04.8767992Z | 2026-10-26T17:27:04.9236701Z | `corr-308f2405e8` |
| 2026-10-26T17:41:46.8916094Z | 2026-10-26T17:41:47.0634584Z | `corr-30bf4c5a5a` |
| 2026-10-26T17:56:29.3672303Z | 2026-10-26T17:56:29.4453526Z | `corr-b4023bda77` |
| 2026-10-26T18:11:11.6075365Z | 2026-10-26T18:11:11.67003Z | `corr-54165230b4` |
| 2026-10-26T18:25:53.8938235Z | 2026-10-26T18:25:53.9561975Z | `corr-225437ecbe` |
| 2026-10-26T18:40:38.4176426Z | 2026-10-26T18:40:38.4801444Z | `corr-82bfc34a18` |
| 2026-10-26T18:55:20.7511821Z | 2026-10-26T18:55:20.9230537Z | `corr-0a9f3bd88c` |
| 2026-10-26T19:10:07.2160309Z | 2026-10-26T19:10:07.2785307Z | `corr-2dfcb2d74b` |
| 2026-10-26T19:25:13.9766453Z | 2026-10-26T19:25:14.0547813Z | `corr-db40310a55` |
| 2026-10-26T19:39:56.5830934Z | 2026-10-26T19:39:56.6299683Z | `corr-871664f8ae` |
| 2026-10-26T19:54:56.4366708Z | 2026-10-26T19:54:56.5147963Z | `corr-5e600abb22` |
| 2026-10-26T20:09:38.8089187Z | 2026-10-26T20:09:38.9808083Z | `corr-e1a2ba654e` |
| 2026-10-26T20:24:21.46463Z | 2026-10-26T20:24:21.5427542Z | `corr-1cac2db72d` |
| 2026-10-26T20:39:03.6921812Z | 2026-10-26T20:39:03.7546805Z | `corr-7549871cd1` |
| 2026-10-26T20:53:50.9932046Z | 2026-10-26T20:53:51.0400791Z | `corr-d0d3f71100` |
| 2026-10-26T21:08:38.3185828Z | 2026-10-26T21:08:38.4123331Z | `corr-57cef15d70` |
| 2026-10-26T21:23:38.5050357Z | 2026-10-26T21:23:38.5675311Z | `corr-2df95563b3` |
| 2026-10-26T21:40:43.2616632Z | 2026-10-26T21:40:43.4179154Z | `corr-5401d7ab38` |

For every row: operation was `Microsoft.CognitiveServices/accounts/listKeys/action`,
scope was the Foundry account, result was `Succeeded` after `Started`, caller
field was pseudonymized as `actor-A`, caller object ID/application ID and
client/user-agent were not returned, and explicit interactive/automated
classification was not returned. The observed periodic pattern is consistent
with extension/toolkit polling, not proof of a specific client. No associated
model deployment or agent operation followed in the same correlation.

## Account, project, exposure, and usage

- **Current inventory:** Seven resources total: five MatchPulse app/monitoring
  resources plus the user-authorized AI Services account and child project.
  The Foundry resources are not part of the MatchPulse runtime.
- **Account:** `AIServices`, SKU `S0`, `Succeeded`; public network access is
  enabled; network ACL default action is `Allow`; local authentication is
  enabled (`disableLocalAuth=false`). A system-assigned identity is present.
- **Project:** `Succeeded`; a system-assigned identity is present. It is the
  account's default project.
- **RBAC:** The read-only account-scope and project-scope role-assignment
  queries returned no assignments at either scope. The query excludes
  inherited assignments from parent scopes; it is not an effective-access
  evaluation. No role was assigned during this review.
- **Deployments:** Foundry deployment listing returned none.
- **Agents:** Agent listing returned HTTP 403 for missing
  `Microsoft.CognitiveServices/accounts/AIServices/agents/read`.
  `NONBLOCKING_OPTIONAL_INTEGRATION_WARNING`. Do not add RBAC merely to clear
  this warning. Agent inventory is unavailable, not evidence that agents do
  not exist.
- **Connections:** The Foundry project connection list returned nine
  registrations. Metadata is summarized below; no credential material or
  raw connection targets were retrieved for this record.
- **Content filters:** Three system-managed Responsible AI policies were
  returned (`Microsoft.Default`, `Microsoft.DefaultV2`, and
  `Microsoft.MAIDefault`). They are system-managed blocking-mode policies;
  category blocking differs by policy. No custom policy was identified by
  this read.
- **Diagnostics:** The account diagnostic-settings list returned an empty
  array.
- **Private endpoints:** ARM reports zero account private endpoint
  connections.
- **Customer-managed keys:** The account ARM representation contained no
  encryption/CMK configuration.
- **Metrics and usage:** For 2026-10-26 14:00–21:00 UTC, account metrics
  reported `FoundryModelEstimatedCost=0`; `TotalCalls=21`, all 21 counted as
  `TotalErrors`, and `SuccessfulCalls=0`. `ModelRequests`, `InputTokens`,
  `OutputTokens`, and `TotalTokens` returned no time series. This is no
  successful model/token usage evidence for that window, but the 21 generic
  failed calls are not classified as model calls and must not be hidden or
  called zero data-plane attempts.
- **Data-plane artifacts:** Files, indexes, vector stores, threads, messages,
  and sessions were not enumerated. The agent/data-plane read returned 403;
  record these checks as `UNAVAILABLE_DUE_TO_DATA_PLANE_RBAC`, not absent.
- **Cost:** Prior resource-group cost/budget readback was $0 month-to-date,
  with a $25 monthly resource-group alert budget and a $50 annual
  subscription alert budget. Resource-ID-filtered account/project cost
  queries returned no rows; this does not prove zero future cost. Existing
  resource-group budget is not a dedicated Foundry usage cap.

## Connection metadata inventory

The project connection API returned connection name, `RemoteTool` category,
auth type, and service target. The table deliberately records only a
non-sensitive target category, not full URLs, connection IDs, or credential
metadata. `Write connections` Activity Log events supplied one start/success
pair per connection, but did not distinguish create from update. The
connection-list response did not expose per-connection created/modified
timestamps; the listed time is the successful write timestamp. For all
connections, credential presence, enabled state, and actual use are
`UNKNOWN`; each belongs to the Foundry project, none is required by MatchPulse,
and any target-side billing would depend on use and provider terms.

| Name | Type / target category | Created / modified | Auth type | Credentials / enabled / used | MatchPulse required | Potential billing |
|---|---|---|---|---|---|---|
| SharePoint | RemoteTool / Microsoft 365 SharePoint | Not distinguished; write succeeded 2026-10-26 14:29:53Z | UnknownConnectionPropertiesV2 | UNKNOWN / UNKNOWN / UNKNOWN | NO | Possible target-side usage if invoked |
| Word | RemoteTool / Microsoft 365 Word | Not distinguished; write succeeded 2026-10-26 14:29:58Z | UnknownConnectionPropertiesV2 | UNKNOWN / UNKNOWN / UNKNOWN | NO | Possible target-side usage if invoked |
| OneDrive | RemoteTool / Microsoft 365 OneDrive | Not distinguished; write succeeded 2026-10-26 14:30:12Z | UnknownConnectionPropertiesV2 | UNKNOWN / UNKNOWN / UNKNOWN | NO | Possible target-side usage if invoked |
| Copilot | RemoteTool / Microsoft 365 Copilot | Not distinguished; write succeeded 2026-10-26 14:30:45Z | UnknownConnectionPropertiesV2 | UNKNOWN / UNKNOWN / UNKNOWN | NO | Possible target-side usage if invoked |
| GitHub | RemoteTool / GitHub MCP | Not distinguished; write succeeded 2026-10-26 14:31:14Z | OAuth2 | UNKNOWN / UNKNOWN / UNKNOWN | NO | Possible target-side usage if invoked |
| MicrosoftMCPServerfor | RemoteTool / Microsoft enterprise MCP | Not distinguished; write succeeded 2026-10-26 14:32:58Z | UnknownConnectionPropertiesV2 | UNKNOWN / UNKNOWN / UNKNOWN | NO | Possible target-side usage if invoked |
| User | RemoteTool / Microsoft 365 user profile | Not distinguished; write succeeded 2026-10-26 14:33:09Z | UnknownConnectionPropertiesV2 | UNKNOWN / UNKNOWN / UNKNOWN | NO | Possible target-side usage if invoked |
| MicrosoftSentinelGraph | RemoteTool / Microsoft Sentinel Graph | Not distinguished; write succeeded 2026-10-26 14:33:38Z | UnknownConnectionPropertiesV2 | UNKNOWN / UNKNOWN / UNKNOWN | NO | Possible target-side usage if invoked |
| MicrosoftSentinelMemoryPrPr | RemoteTool / Microsoft Sentinel memory | Not distinguished; write succeeded 2026-10-26 14:33:48Z | UnknownConnectionPropertiesV2 | UNKNOWN / UNKNOWN / UNKNOWN | NO | Possible target-side usage if invoked |

## MatchPulse runtime dependency evidence

`MATCHPULSE_RUNTIME_DEPENDENCY=NO`. Repository search in `src`, `infra`, and
`scripts` found no literal Foundry account/project name, their project
endpoint, Hosted/Prompt Agent ID, Foundry connection ID, or model deployment
ID. MatchPulse Bicep does not declare either Foundry resource. It has only a
generic, optional Foundry adapter configuration; `foundryRuntimeMode` defaults
to `off`, and the deployed image has no Foundry endpoint/deployment
configuration. The submitted deterministic workflow does not use this
separate development project. Preserve the accurate disclosure:

> Foundry runtime is disabled in the submitted MatchPulse deployment, and
> the demonstrated workflow makes zero model calls.

The approved video does not demonstrate Foundry usage.

## Post-submission review only — no current action authorized

Current recommendation: `RETAIN_PENDING_POST_SUBMISSION_REVIEW`. Do not modify,
delete, deploy to, create an agent in, assign RBAC to, or rotate credentials
for these resources as part of submission finalization. After challenge
submission, perform a separately authorized cost and security review and
select among:

- `RETAIN_AND_SECURE`: verify owner, connection necessity/permissions, add
  private networking and disable local authentication if compatible, add
  explicit budget/alerts, and put Foundry resources in a separate resource
  group or separate Bicep module for future development.
- `QUARANTINE_THEN_DELETE`: first separately approve and validate containment,
  dependencies, and evidence retention; only then decide on deletion.
- `IMMEDIATE_DELETE`: consider only after an explicit post-submission approval
  and dependency/data-retention review; not recommended during submission.

The review should assess restricting public network access, disabling local
authentication, removing unused remote-tool connections, dedicated budget
controls, bringing resources under separate Bicep ownership, and deleting the
project/account if no longer needed. No item in this future checklist is
authorized now.
