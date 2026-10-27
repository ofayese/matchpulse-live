# MatchPulse Live Azure cost plan

This is a planning estimate, not a price quote or spend limit. Rates below were
retrieved from Microsoft's Retail Prices API and public service pricing for
East US 2 on October 23, 2026. Prices are USD and exclude taxes/support.

## Metered rates and assumptions

- Container Apps Consumption: active vCPU $0.000024 per vCPU-second; active
  memory $0.000003 per GiB-second; requests $0.40 per million. The planned app
  uses 0.5 vCPU and 1 GiB, or $0.054 per active hour. First-month free grants
  are not assumed because billing-account eligibility and remaining balance
  are unknown.
- Log Analytics: $2.76/GB ingestion; the workspace daily cap is 0.023 GB/day.
  Seven days at the cap is 0.161 GB, or $0.44436 before any account-level
  allowance. The first 5 GB/month account allowance may reduce this to zero;
  eligibility and balance are unknown. Application Insights workspace
  ingestion is not counted again.
- GPT-4o-mini regional input: $0.165/1M tokens; output: $0.66/1M tokens.
- Egress: assume below the public 100 GB/month allowance; actual eligibility
  is unknown, and transfer cost is conservatively recorded as $0 for these
  small scenarios.
- No dedicated Container Apps profile, private endpoint, Event Hubs, ACR, or
  Azure storage is included.
- Uvicorn access logging is disabled; application logs use warning level. ACA
  platform system logs remain available. No HTTP diagnostic categories or
  Application Insights sampling parameter is configured; the app does not ship
  an Azure Monitor OpenTelemetry exporter in this deployment.

## Scenarios

| Scenario | Seven-day operating assumptions | Before free allowances |
| --- | --- | ---: |
| Demo only | 20 model calls, 500 input/300 output tokens each, 2 active hours, .02 GB logs | $0.168818 |
| Expected judging | 100 calls, 800/500 tokens, 2 active hours including 30 cold starts, .10 GB logs | $0.430240 |
| Constrained operating target | Maximum 80 calls total by operator log, each request bounded to 4 KiB input payload/128 output tokens, 14 active hours total (2/day), 500 ACA requests, 0.023 GB/day cap | $1.261386 |

Scenario A cost after all applicable free allowances: $0.005610 model cost;
compute, requests and logs assumed covered. Scenario B after the free Log
Analytics allowance would be about $0.154240 before any ACA grant. Scenario C
after the log allowance would be about $0.817026 before ACA grants.

The application enforces at most 20 model calls in one process, one concurrent
model request, one HTTP attempt (no retries), a 1.4-second timeout, a 128-token
completion ceiling, and a 4 KiB serialized UTF-8 prompt-size ceiling. That byte
ceiling is a conservative input-token proxy, not model-tokenizer accounting.
The counter resets on process restart. The 80-call Scenario C limit therefore
requires operator tracking across restarts; it is not a technical hard limit.

**Artifact identity:** the currently deployed image is
`ghcr.io/ofayese/matchpulse-live@sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226`,
associated with source
`335781f928011f99a644083d80bfe4dfc480b1a6` and attestation `59336499`.
The fresh read-only Azure check on 2026-10-26 confirmed that the deployed app
still uses this digest and has no ingress configuration. The fresh, paginated resource-group inventory returned seven resources: the
five previously observed app/monitoring resources plus an unexpected
Cognitive Services account and child Foundry project. They were explicitly
created after the Container App deployment and are not in Bicep or required
by the app. This is `AZURE_COUNT_RECONCILED_UNEXPECTED_RESOURCES`; owner/
security review and a separate disposition remain outstanding. No model
deployments were found, and the app's environment-variable names contain no
Foundry setting. A recorded run had zero model calls. Hosted-agent inventory
was not available because the optional Hosted Agents Preview returned 403.
The direct resource-group RBAC query returned no assignments. Current
month-to-date spend is $0 USD; the $25 monthly resource-group budget has $0
actual and forecast, while the separate $50 annual subscription budget has
$0 actual and no returned forecast. These are alerts, not spending limits;
the $15 operational stop threshold is not enforced by Azure. The resource
group cost query returned only the workspace at $0 and did not itemize
account/project usage; resource-ID-filtered month-to-date queries for the
additional account and project returned no rows. This does not establish zero
future or usage-based cost. The artifact attestation was not independently
revalidated during this check.

The Log Analytics workspace has a 30-day default retention and 0.023 GB/day
quota. The linked Application Insights component reports 90 days, and a
direct table-list read confirms 90-day retention for its core telemetry
tables. Workspace-based Application Insights is stored/billed through Log
Analytics, with retention set at workspace/table scope; see
[Microsoft Learn](https://learn.microsoft.com/en-us/azure/azure-monitor/app/create-workspace-resource)
and [Log Analytics retention](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/data-retention-configure).
Source inspection confirms the 4 KiB and 128-token controls are present at the
recorded source revision. The Bicep call budget, concurrency and timeout
environment values are separate configuration.

For planning confidence, use a 0.5x–2x sensitivity range on each seven-day point estimate: A $0.084–$0.338, B $0.215–$0.860, and C $0.631–$2.523 before free allowances. This is a sensitivity range, not a statistical confidence interval, and excludes daily-cap overshoot, extended runtime, and untracked calls. Confidence is medium for arithmetic at observed rates and low for actual spend because real traffic, ingestion, pricing changes, and free-credit eligibility are unknown. The constrained estimate and sensitivity range are below $25 for the planned seven-day challenge window only if operating assumptions are followed. No Azure budget or telemetry cap is a guaranteed cutoff. Daily cost review and scale-to-zero are required;
shut down if the forecast reaches $25 or an unexplained ingestion/call increase
appears.

## Monthly usage estimates

These estimates use a 30-day month, the rates above, and no free grants. They
exclude taxes and cap overshoot. The zero-usage row assumes no active replica,
model calls, requests, or ingested logs; Azure platform logs may make actual
telemetry spend nonzero.

| Scenario | Monthly assumptions | Estimated total |
| --- | --- | ---: |
| Zero use | 0 active hours, no requests/inference/log ingestion | $0.00 workload cost; up to $1.90 if the workspace ingests at its daily cap |
| Low use | 1 active hour/day, 100 requests/day, 10 model calls/day at 500 input/300 output tokens, 0.10 GB logs/month | $1.98 |
| Demo use | 2 active hours/day, 500 requests/day, 20 model calls/day at 500 input/300 output tokens, 0.023 GB logs/day | $5.32 |

The low-use calculation is $1.62 compute + $0.0012 requests + $0.08415
inference + $0.276 logs. Demo use is $3.24 compute + $0.006 requests +
$0.1683 inference + $1.9044 logs. Estimates exclude cap overshoot and use
pre-free-allowance rates. A live deployment still needs daily cost review and
an explicit operator stop procedure.

## Monthly accidental-running projection

If one replica remains active for 30 days, compute is about $38.88. At the
0.023 GB/day cap, Log Analytics is up to about $1.9044 before overshoot. Assuming
20 model calls/day across restarts and 4 KiB/128 tokens per call adds about
$0.4562; 15,000 API requests adds about $0.006. Approximate total: **$41.25**
before possible cap overshoot and applicable free allowances. This exceeds the
existing $25 monthly budget alert. The budget is an alert only.

Sources: [Retail Prices API](https://learn.microsoft.com/rest/api/cost-management/retail-prices/azure-retail-prices),
[Container Apps billing](https://learn.microsoft.com/azure/container-apps/billing),
[Azure Monitor pricing](https://azure.microsoft.com/en-us/pricing/details/monitor/),
[Log Analytics quota minimum](https://learn.microsoft.com/cli/azure/monitor/log-analytics/workspace?view=azure-cli-latest),
[daily cap limits](https://learn.microsoft.com/azure/azure-monitor/logs/daily-cap),
[Azure OpenAI quota units](https://learn.microsoft.com/azure/foundry/openai/how-to/quota).
