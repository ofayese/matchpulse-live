#!/usr/bin/env python3
"""Static guardrails for the compiled challenge Bicep template."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_template.py <compiled-arm-template>", file=sys.stderr)
        return 2
    template = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    template_text = json.dumps(template)
    params: dict[str, Any] = template["parameters"]
    resources: list[dict[str, Any]] = template["resources"]
    kinds = {resource["type"].lower() for resource in resources}

    checks = {
        "monitoring defaults on": params["monitoringEnabled"]["defaultValue"] is True,
        "workspace retention is locked to 30 days": params["logRetentionDays"].get("allowedValues") == [30],
        "unsupported retention values are rejected by the parameter schema": params["logRetentionDays"].get("allowedValues") == [30],
        "daily quota defaults to minimum supported value": params["logDailyQuotaGb"]["defaultValue"] == "0.023",
        "daily quota parameter accepts only approved values": params["logDailyQuotaGb"].get("allowedValues") == ["0.023", "0.05", "0.1", "1"],
        "unsupported daily quotas are rejected by the parameter schema": params["logDailyQuotaGb"].get("allowedValues") == ["0.023", "0.05", "0.1", "1"],
        "model calls capped per process": params["foundryCallBudget"].get("maxValue") == 20,
        "model maximum replicas remains one": params["maxReplicas"].get("minValue") == 1 and params["maxReplicas"].get("maxValue") == 1,
        "workspace uses supported direct capping property": "microsoft.operationalinsights/workspaces" in kinds,
        "no quota child resource": not any("/quotas" in kind for kind in kinds),
        "no Event Hubs resource": not any("eventhub" in kind for kind in kinds),
        "no ACR resource": not any("containerregistries" in kind for kind in kinds),
        "system-assigned identity": any(resource.get("identity", {}).get("type") == "SystemAssigned" for resource in resources),
        "synthetic-only remains enabled": "CHALLENGE_SYNTHETIC_ONLY" in template_text and "'true'" in template_text,
        "public HTTPS ingress on port 8080": '"external": true' in template_text and '"transport": "httpsOnly"' in template_text and '"targetPort": 8080' in template_text,
        "Foundry calls are serialized and bounded": "FOUNDRY_MAX_CONCURRENCY" in template_text and "FOUNDRY_CALL_BUDGET" in template_text and "'1'" in template_text,
        "Foundry request timeout is bounded": "FOUNDRY_TIMEOUT_SECONDS" in template_text and "'1.4'" in template_text,
    }

    workspace = next(resource for resource in resources if resource["type"].lower() == "microsoft.operationalinsights/workspaces")
    cap = workspace["properties"]["workspaceCapping"]["dailyQuotaGb"]
    checks["workspace cap is parameterized"] = "json(parameters('logDailyQuotaGb'))" in cap
    checks["monitoring resources are conditional"] = all(
        resource.get("condition") == "[parameters('monitoringEnabled')]"
        for resource in resources
        if resource["type"].lower() in {
            "microsoft.operationalinsights/workspaces",
            "microsoft.insights/components",
        }
    )
    environment = next(resource for resource in resources if resource["type"].lower() == "microsoft.app/managedenvironments")
    app_logs_expression = environment["properties"]["appLogsConfiguration"]
    checks["monitoring-disabled environment uses no log destination"] = "parameters('monitoringEnabled')" in app_logs_expression and "'none'" in app_logs_expression
    bicep_source = Path(__file__).with_name("main.bicep").read_text(encoding="utf-8")
    checks["monitoring-disabled path has null-safe monitoring references"] = "logs!." in bicep_source and "insights!." in bicep_source
    param_example = json.loads(Path(__file__).with_name("main.parameters.example.json").read_text(encoding="utf-8"))
    example = param_example["parameters"]
    image = example["image"]["value"]
    checks["example image is pinned to SHA-256 digest"] = bool(
        re.fullmatch(r"ghcr\.io/ofayese/matchpulse-live@sha256:[0-9a-f]{64}", image)
    )
    checks["model-enabled parameters use managed identity"] = example["foundryAuthMode"]["value"] == "managed_identity"

    failures = [name for name, passed in checks.items() if not passed]
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
    if failures:
        print(f"{len(failures)} infrastructure validation check(s) failed", file=sys.stderr)
        return 1
    print(f"PASS: {len(checks)} infrastructure guardrails")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
