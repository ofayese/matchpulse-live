#!/usr/bin/env python3
"""Static guardrails for the compiled challenge Bicep template."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

LOG_WORKSPACE_TYPE = "microsoft.operationalinsights/workspaces"
FOUNDATION_RESOURCE_TYPES = {
    LOG_WORKSPACE_TYPE,
    "microsoft.insights/components",
    "microsoft.app/managedenvironments",
}
APP_RESOURCE_TYPE = "microsoft.app/containerapps"
FORBIDDEN_RESOURCE_TOKENS = (
    "authorization/roleassignments",
    "cognitiveservices",
    "machinelearning",
    "foundry",
    "containerregistries",
    "eventhub",
    "storageaccounts",
    "microsoft.sql/",
    "dbforpostgresql",
    "documentdb",
    "cache/redis",
    "keyvault/vaults",
    "microsoft.network/",
)


def _monitoring_checks(
    params: dict[str, Any],
    workspace: dict[str, Any],
    insights: dict[str, Any],
    environment: dict[str, Any],
    kinds: set[str],
    template_text: str,
) -> dict[str, bool]:
    quota = params["logDailyQuotaGb"]
    retention = params["logRetentionDays"]
    call_budget = params["foundryCallBudget"]
    max_replicas = params["maxReplicas"]
    cap = workspace["properties"]["workspaceCapping"]["dailyQuotaGb"]
    environment_properties = environment["properties"]
    return {
        "workspace retention is locked to 30 days": (
            retention.get("allowedValues") == [30]
        ),
        "Application Insights uses Log Analytics": (
            insights["properties"]["IngestionMode"] == "LogAnalytics"
        ),
        "retained peer-security settings are explicit": (
            environment_properties["peerAuthentication"]["mtls"]["enabled"]
            is False
            and environment_properties["peerTrafficConfiguration"][
                "encryption"
            ]["enabled"]
            is False
        ),
        "daily quota defaults to minimum supported value": (
            quota["defaultValue"] == "0.023"
        ),
        "daily quota parameter accepts only approved values": (
            quota.get("allowedValues") == ["0.023", "0.05", "0.1", "1"]
        ),
        "unsupported daily quotas are rejected by the parameter schema": (
            quota.get("allowedValues") == ["0.023", "0.05", "0.1", "1"]
        ),
        "model calls capped per process": call_budget.get("maxValue") == 20,
        "model maximum replicas remains one": (
            max_replicas.get("minValue") == 1
            and max_replicas.get("maxValue") == 1
        ),
        "workspace uses supported direct capping property": (
            LOG_WORKSPACE_TYPE in kinds
        ),
        "no quota child resource": not any(
            "/quotas" in kind for kind in kinds
        ),
        "Foundry calls are serialized and bounded": (
            "FOUNDRY_MAX_CONCURRENCY" in template_text
            and "FOUNDRY_CALL_BUDGET" in template_text
            and "'1'" in template_text
        ),
        "Foundry request timeout is bounded": (
            "FOUNDRY_TIMEOUT_SECONDS" in template_text
            and "'1.4'" in template_text
        ),
        "workspace cap is parameterized": (
            "json(parameters('logDailyQuotaGb'))" in cap
        ),
    }


def _resource_checks(
    template: dict[str, Any],
    params: dict[str, Any],
    resources: list[dict[str, Any]],
    kinds: set[str],
    app: dict[str, Any],
    bicep_source: str,
) -> dict[str, bool]:
    app_properties = app["properties"]
    container = app_properties["template"]["containers"][0]
    ingress = app_properties["configuration"]["ingress"]
    scale = app_properties["template"]["scale"]
    image = json.loads(
        Path(__file__)
        .with_name("main.parameters.example.json")
        .read_text(encoding="utf-8")
    )["parameters"]["image"]["value"]
    probes = {
        (probe["type"], probe["httpGet"]["path"], probe["httpGet"]["port"])
        for probe in container["probes"]
    }
    expected_probes = {
        ("Liveness", "/health/live", 8080),
        ("Readiness", "/health/ready", 8080),
        ("Startup", "/health/live", 8080),
    }
    deployment_mode = params["deployFoundationResources"]
    return {
        "clean mode defaults to foundation deployment": (
            deployment_mode["defaultValue"] is True
        ),
        "clean mode contains exactly the four approved resources": (
            len(resources) == 4
            and kinds == FOUNDATION_RESOURCE_TYPES | {APP_RESOURCE_TYPE}
        ),
        "no Smart Detection action group": not any(
            "microsoft.insights/actiongroups" in kind for kind in kinds
        ),
        "no Azure-generated App Insights compatibility metadata": (
            '"Flow_Type"' not in json.dumps(template)
            and '"Request_Source"' not in json.dumps(template)
        ),
        "no unapproved Azure resource families": not any(
            token in kind
            for kind in kinds
            for token in FORBIDDEN_RESOURCE_TOKENS
        ),
        "foundation resources are conditional on deployFoundationResources": (
            all(
                resource.get("condition")
                == "[parameters('deployFoundationResources')]"
                for resource in resources
                if resource["type"].lower() in FOUNDATION_RESOURCE_TYPES
            )
        ),
        "obsolete monitoringEnabled parameter is absent": (
            "monitoringEnabled" not in params
        ),
        "system-assigned Container App identity": (
            app.get("identity", {}).get("type") == "SystemAssigned"
        ),
        "synthetic-only remains enabled": (
            "CHALLENGE_SYNTHETIC_ONLY" in bicep_source
            and "value: 'true'" in bicep_source
        ),
        "external HTTPS ingress uses approved settings": (
            ingress["external"] is True
            and ingress["targetPort"] == 8080
            and ingress["transport"] == "auto"
            and ingress["allowInsecure"] is False
        ),
        "Container App uses the approved immutable image": (
            image
            == "ghcr.io/ofayese/matchpulse-live@sha256:"
            "f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226"
            and container["image"] == "[parameters('image')]"
        ),
        "Container App resources are 0.5 CPU and 1Gi": (
            container["resources"]["cpu"] == "[json('0.5')]"
            and container["resources"]["memory"] == "1Gi"
        ),
        "Container App replicas remain zero to one": (
            params["minReplicas"]["defaultValue"] == 0
            and params["minReplicas"].get("minValue") == 0
            and params["maxReplicas"]["defaultValue"] == 1
            and params["maxReplicas"].get("minValue") == 1
            and params["maxReplicas"].get("maxValue") == 1
            and scale["minReplicas"] == "[parameters('minReplicas')]"
            and scale["maxReplicas"] == "[parameters('maxReplicas')]"
        ),
        "Container App retains approved health probes": (
            probes == expected_probes
        ),
        "Foundry remains off with an empty endpoint": (
            params["foundryRuntimeMode"]["defaultValue"] == "off"
            and params["foundryEndpoint"]["defaultValue"] == ""
        ),
        "existing resources have identity-only declarations": all(
            declaration in bicep_source
            for declaration in (
                "resource logWorkspaceExisting "
                "'Microsoft.OperationalInsights/workspaces@2025-02-01' "
                "existing = {\n  name: workspaceName\n}",
                "resource appInsightsExisting "
                "'Microsoft.Insights/components@2020-02-02' "
                "existing = {\n  name: insightsName\n}",
                "resource environmentExisting "
                "'Microsoft.App/managedEnvironments@2024-03-01' "
                "existing = {\n  name: environmentName\n}",
            )
        ),
        "environment retains Log Analytics destination": (
            "destination: 'log-analytics'" in bicep_source
        ),
        "Container App uses a scope-relative environment ID": (
            "resourceId('Microsoft.App/managedEnvironments', environmentName)"
            in bicep_source
            and "managedEnvironmentId: selectedEnvironmentId" in bicep_source
        ),
        "App Insights connection string is used only as the app secret": (
            "var selectedAppInsightsConnectionString =" in bicep_source
            and "deployFoundationResources" in bicep_source
            and "value: selectedAppInsightsConnectionString" in bicep_source
            and "secretRef: 'applicationinsights-connection-string'"
            in bicep_source
            and bicep_source.count("selectedAppInsightsConnectionString") == 2
            and not re.search(
                r"(?m)^output .*ConnectionString", bicep_source
            )
        ),
    }


def _parameter_checks(example: dict[str, Any]) -> dict[str, bool]:
    image = example["image"]["value"]
    return {
        "example image is pinned to SHA-256 digest": bool(
            re.fullmatch(
                r"ghcr\.io/ofayese/matchpulse-live@sha256:[0-9a-f]{64}",
                image,
            )
        ),
        "model-enabled parameters use managed identity": (
            example["foundryAuthMode"]["value"] == "managed_identity"
        ),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "usage: validate_template.py <compiled-arm-template>",
            file=sys.stderr,
        )
        return 2
    template = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    params: dict[str, Any] = template["parameters"]
    resources: list[dict[str, Any]] = template["resources"]
    kinds = {resource["type"].lower() for resource in resources}
    resource_by_type = {
        resource["type"].lower(): resource for resource in resources
    }
    bicep_source = Path(__file__).with_name("main.bicep").read_text(
        encoding="utf-8"
    )
    example = json.loads(
        Path(__file__)
        .with_name("main.parameters.example.json")
        .read_text(encoding="utf-8")
    )["parameters"]
    checks = {
        **_monitoring_checks(
            params,
            resource_by_type[LOG_WORKSPACE_TYPE],
            resource_by_type["microsoft.insights/components"],
            resource_by_type["microsoft.app/managedenvironments"],
            kinds,
            json.dumps(template),
        ),
        **_resource_checks(
            template,
            params,
            resources,
            kinds,
            resource_by_type[APP_RESOURCE_TYPE],
            bicep_source,
        ),
        **_parameter_checks(example),
    }

    failures = [name for name, passed in checks.items() if not passed]
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
    if failures:
        print(
            f"{len(failures)} infrastructure validation check(s) failed",
            file=sys.stderr,
        )
        return 1
    print(f"PASS: {len(checks)} infrastructure guardrails")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
