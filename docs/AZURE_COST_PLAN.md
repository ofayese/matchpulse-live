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

**Artifact limitation:** those new 4 KiB and 128-token source controls are not
present in the supplied immutable GHCR digest
`1bb9df336d95a5549f7384e023c5954710c662f59d6fb9b9ac2d72ed3ee0c96c`. The
planning repo changes do not rebuild or republish that accepted image. The
deployed image must be replaced by a separately reviewed, newly built immutable
digest before those two controls can be claimed for Azure. The Bicep call
budget, concurrency and timeout environment values are separate configuration.

For planning confidence, use a 0.5x–2x sensitivity range on each seven-day point estimate: A $0.084–$0.338, B $0.215–$0.860, and C $0.631–$2.523 before free allowances. This is a sensitivity range, not a statistical confidence interval, and excludes daily-cap overshoot, extended runtime, and untracked calls. Confidence is medium for arithmetic at observed rates and low for actual spend because real traffic, ingestion, pricing changes, and free-credit eligibility are unknown. The constrained estimate and sensitivity range are below $25 for the planned seven-day challenge window only if operating assumptions are followed. No Azure budget or telemetry cap is a guaranteed cutoff. Daily cost review and scale-to-zero are required;
shut down if the forecast reaches $25 or an unexplained ingestion/call increase
appears.

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
