#!/usr/bin/env python3
from __future__ import annotations

import argparse
import getpass
import json
import os
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Any


TASKFILE_VARS_KEYS = (
    "DOMAIN_NAME_DEFAULT",
    "DNS_SUBDOMAIN_LABELS",
    "CLOUDFLARE_ZONE_ID_DEFAULT",
)

DOMAIN_PATTERN = re.compile(
    r"^(?!-)[a-z0-9-]{1,63}(?<!-)(\.(?!-)[a-z0-9-]{1,63}(?<!-))+$"
)
LABEL_PATTERN = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")


@dataclass(frozen=True)
class TaskfileDefaults:
    domain_name: str
    subdomain_labels: list[str]
    cloudflare_zone_id: str


def normalize_dns_name(value: str) -> str:
    return value.strip().lower().rstrip(".")


def parse_taskfile_defaults(taskfile_content: str) -> TaskfileDefaults:
    try:
        import yaml
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Missing dependency 'PyYAML'. Install infra dependencies."
        ) from error

    parsed = yaml.safe_load(taskfile_content) or {}
    vars_block = parsed.get("vars")
    if not isinstance(vars_block, dict):
        raise ValueError("Taskfile vars block is missing or invalid")

    parsed_values: dict[str, str] = {}
    for key in TASKFILE_VARS_KEYS:
        value = vars_block.get(key)
        if value is None:
            continue
        parsed_values[key] = str(value).strip()

    missing_keys = [key for key in TASKFILE_VARS_KEYS if not parsed_values.get(key)]
    if missing_keys:
        raise ValueError("Missing required Taskfile vars: " + ", ".join(missing_keys))

    labels_raw = vars_block.get("DNS_SUBDOMAIN_LABELS")
    if isinstance(labels_raw, list):
        labels = [str(label).strip() for label in labels_raw if str(label).strip()]
    else:
        labels = [
            label.strip()
            for label in str(parsed_values["DNS_SUBDOMAIN_LABELS"]).split(",")
            if label.strip()
        ]
    if not labels:
        raise ValueError("DNS_SUBDOMAIN_LABELS must contain at least one label")

    return TaskfileDefaults(
        domain_name=normalize_dns_name(parsed_values["DOMAIN_NAME_DEFAULT"]),
        subdomain_labels=labels,
        cloudflare_zone_id=parsed_values["CLOUDFLARE_ZONE_ID_DEFAULT"],
    )


def load_taskfile_defaults(taskfile_path: pathlib.Path) -> TaskfileDefaults:
    return parse_taskfile_defaults(taskfile_path.read_text(encoding="utf-8"))


def build_desired_cname_records(
    domain_name: str, subdomain_labels: list[str]
) -> list[dict[str, Any]]:
    normalized_domain = normalize_dns_name(domain_name)
    return [
        {
            "type": "CNAME",
            "name": f"{label}.{normalized_domain}",
            "content": normalized_domain,
        }
        for label in subdomain_labels
    ]


def validate_dns_inputs(domain_name: str, labels: list[str]) -> None:
    normalized_domain = normalize_dns_name(domain_name)
    if not DOMAIN_PATTERN.match(normalized_domain):
        raise ValueError(f"Invalid domain name: {domain_name}")

    if not labels:
        raise ValueError("No DNS labels provided")

    for label in labels:
        normalized_label = label.strip().lower()
        if not LABEL_PATTERN.match(normalized_label):
            raise ValueError(f"Invalid DNS label: {label}")


def plan_cname_changes(
    desired_records: list[dict[str, Any]],
    existing_records: list[dict[str, Any]],
    ttl: int,
    proxied: bool,
    delete_stale: bool,
    domain_scope: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    desired_by_name = {
        normalize_dns_name(record["name"]): {
            **record,
            "name": normalize_dns_name(record["name"]),
            "content": normalize_dns_name(record["content"]),
        }
        for record in desired_records
    }

    normalized_domain_scope = normalize_dns_name(domain_scope or "")
    existing_by_name: dict[str, dict[str, Any]] = {}
    for record in existing_records:
        if normalize_dns_name(str(record.get("type", ""))) != "cname":
            continue

        normalized_name = normalize_dns_name(str(record.get("name", "")))
        if normalized_domain_scope and not normalized_name.endswith(
            f".{normalized_domain_scope}"
        ):
            continue

        existing_by_name[normalized_name] = {
            **record,
            "name": normalized_name,
            "content": normalize_dns_name(str(record.get("content", ""))),
        }

    create: list[dict[str, Any]] = []
    update: list[dict[str, Any]] = []
    delete: list[dict[str, Any]] = []

    for name, desired in desired_by_name.items():
        existing = existing_by_name.get(name)
        payload = {
            "type": "CNAME",
            "name": name,
            "content": desired["content"],
            "ttl": ttl,
            "proxied": proxied,
        }

        if existing is None:
            create.append(payload)
            continue

        if (
            normalize_dns_name(str(existing.get("content", "")))
            != normalize_dns_name(payload["content"])
            or int(existing.get("ttl", ttl)) != payload["ttl"]
            or bool(existing.get("proxied", proxied)) != payload["proxied"]
        ):
            update.append({"id": existing["id"], **payload})

    if delete_stale:
        for name, existing in existing_by_name.items():
            if name not in desired_by_name:
                delete.append(existing)

    return {"create": create, "update": update, "delete": delete}


class CloudflareClient:
    def __init__(
        self,
        api_token: str | None = None,
        api_key: str | None = None,
        api_email: str | None = None,
        sdk_client: Any | None = None,
        request_timeout_seconds: float = 30.0,
    ):
        if sdk_client is None:
            try:
                from cloudflare import Cloudflare
            except ModuleNotFoundError as error:
                raise RuntimeError(
                    "Missing dependency 'cloudflare'. Install infra dependencies first."
                ) from error

            if api_token:
                self.sdk = Cloudflare(
                    api_token=api_token,
                    timeout=request_timeout_seconds,
                )
            elif api_key and api_email:
                self.sdk = Cloudflare(
                    api_key=api_key,
                    api_email=api_email,
                    timeout=request_timeout_seconds,
                )
            else:
                raise ValueError(
                    "Missing Cloudflare auth. Provide api token or api key + api email."
                )
        else:
            self.sdk = sdk_client

    @staticmethod
    def _handle_sdk_error(error: Exception) -> RuntimeError:
        message = str(error)
        if "Unable to authenticate request" in message or "code': 10001" in message:
            return RuntimeError(
                "Cloudflare authentication failed. Use a valid API token with Zone DNS edit/read permissions, or use --api-key with --api-email."
            )
        return RuntimeError(f"Cloudflare API request failed: {message}")

    @staticmethod
    def _extract(obj: Any, key: str, default: Any) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    @staticmethod
    def _to_plain_record(record: Any) -> dict[str, Any]:
        if isinstance(record, dict):
            return record
        if hasattr(record, "model_dump"):
            return record.model_dump(exclude_none=True)
        return {
            "id": getattr(record, "id", None),
            "name": getattr(record, "name", None),
            "type": getattr(record, "type", None),
            "content": getattr(record, "content", None),
            "ttl": getattr(record, "ttl", None),
            "proxied": getattr(record, "proxied", None),
        }

    def list_cname_records(self, zone_id: str) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        page = 1
        per_page = 500

        try:
            while True:
                response = self.sdk.dns.records.list(
                    zone_id=zone_id,
                    type="CNAME",
                    page=page,
                    per_page=per_page,
                )
                response_records = self._extract(response, "result", [])
                records.extend(
                    self._to_plain_record(record) for record in response_records
                )
                result_info = self._extract(response, "result_info", {})
                total_pages = self._extract(result_info, "total_pages", 1)
                if page >= int(total_pages):
                    break
                page += 1
        except Exception as error:
            raise self._handle_sdk_error(error) from error

        return records

    def create_dns_record(self, zone_id: str, payload: dict[str, Any]) -> None:
        try:
            self.sdk.dns.records.create(zone_id=zone_id, **payload)
        except Exception as error:
            raise self._handle_sdk_error(error) from error

    def update_dns_record(
        self, zone_id: str, record_id: str, payload: dict[str, Any]
    ) -> None:
        payload_without_id = {k: v for k, v in payload.items() if k != "id"}
        try:
            self.sdk.dns.records.update(
                record_id, zone_id=zone_id, **payload_without_id
            )
        except Exception as error:
            raise self._handle_sdk_error(error) from error

    def delete_dns_record(self, zone_id: str, record_id: str) -> None:
        try:
            self.sdk.dns.records.delete(record_id, zone_id=zone_id)
        except Exception as error:
            raise self._handle_sdk_error(error) from error


def sync_cname_records(
    client: CloudflareClient,
    zone_id: str,
    desired_records: list[dict[str, Any]],
    *,
    ttl: int,
    proxied: bool,
    delete_stale: bool,
    dry_run: bool,
    domain_scope: str,
) -> dict[str, list[dict[str, Any]]]:
    existing = client.list_cname_records(zone_id)
    plan = plan_cname_changes(
        desired_records=desired_records,
        existing_records=existing,
        ttl=ttl,
        proxied=proxied,
        delete_stale=delete_stale,
        domain_scope=domain_scope,
    )

    if dry_run:
        return plan

    for payload in plan["create"]:
        client.create_dns_record(zone_id, payload)

    for payload in plan["update"]:
        client.update_dns_record(zone_id, payload["id"], payload)

    for payload in plan["delete"]:
        client.delete_dns_record(zone_id, payload["id"])

    return plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Update Cloudflare CNAME records from Taskfile DNS defaults"
    )
    parser.add_argument(
        "--taskfile",
        default=str(pathlib.Path(__file__).resolve().parents[2] / "Taskfile.yml"),
        help="Path to Taskfile containing DOMAIN_NAME_DEFAULT and DNS_SUBDOMAIN_LABELS",
    )
    parser.add_argument("--zone-id", help="Cloudflare zone ID override")
    parser.add_argument("--domain", help="Domain override")
    parser.add_argument("--labels", help="Comma-separated subdomain labels override")
    parser.add_argument("--api-token", help="Cloudflare API token override")
    parser.add_argument("--api-key", help="Cloudflare global API key override")
    parser.add_argument("--api-email", help="Cloudflare account email for API key")
    parser.add_argument("--ttl", type=int, default=60, help="Record TTL in seconds")
    parser.add_argument(
        "--request-timeout",
        type=float,
        default=30.0,
        help="Cloudflare API timeout in seconds",
    )
    parser.add_argument(
        "--proxied",
        action="store_true",
        default=False,
        help="Enable Cloudflare proxy",
    )
    parser.add_argument(
        "--delete-stale",
        action="store_true",
        default=False,
        help="Delete existing CNAME records not present in DNS_SUBDOMAIN_LABELS",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show create/update/delete plan without making Cloudflare API changes",
    )
    parser.add_argument(
        "--output",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )
    return parser


def resolve_api_token(cli_token: str | None) -> str:
    if cli_token and cli_token.strip():
        return cli_token.strip()

    env_token = os.getenv("CLOUDFLARE_API_TOKEN") or os.getenv("CF_API_TOKEN")
    if env_token and env_token.strip():
        return env_token.strip()

    if sys.stdin.isatty():
        prompted_token = getpass.getpass("Cloudflare API token: ").strip()
        if prompted_token:
            return prompted_token

    raise ValueError(
        "Cloudflare API token missing. Provide --api-token, set CLOUDFLARE_API_TOKEN, or enter when prompted."
    )


def resolve_cloudflare_auth(
    cli_token: str | None,
    cli_api_key: str | None,
    cli_api_email: str | None,
) -> dict[str, str]:
    token = cli_token or os.getenv("CLOUDFLARE_API_TOKEN") or os.getenv("CF_API_TOKEN")
    if token and token.strip():
        return {"api_token": token.strip()}

    api_key = cli_api_key or os.getenv("CLOUDFLARE_API_KEY") or os.getenv("CF_API_KEY")
    api_email = (
        cli_api_email or os.getenv("CLOUDFLARE_API_EMAIL") or os.getenv("CF_API_EMAIL")
    )
    if api_key and api_key.strip():
        if not api_email or not api_email.strip():
            raise ValueError(
                "Cloudflare API email missing for API key auth. Use --api-email or CF_API_EMAIL."
            )
        return {"api_key": api_key.strip(), "api_email": api_email.strip()}

    if sys.stdin.isatty():
        prompted_token = getpass.getpass("Cloudflare API token: ").strip()
        if prompted_token:
            return {"api_token": prompted_token}

    raise ValueError(
        "Cloudflare auth missing. Provide --api-token, set CLOUDFLARE_API_TOKEN, or use --api-key with --api-email."
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        defaults = load_taskfile_defaults(pathlib.Path(args.taskfile))
        domain_name = normalize_dns_name(args.domain or defaults.domain_name)
        zone_id = args.zone_id or defaults.cloudflare_zone_id

        if args.labels:
            labels = [
                label.strip().lower()
                for label in args.labels.split(",")
                if label.strip()
            ]
        else:
            labels = [label.strip().lower() for label in defaults.subdomain_labels]

        validate_dns_inputs(domain_name, labels)

        auth = resolve_cloudflare_auth(args.api_token, args.api_key, args.api_email)

        desired_records = build_desired_cname_records(domain_name, labels)
        client = CloudflareClient(
            request_timeout_seconds=args.request_timeout,
            **auth,
        )
        plan = sync_cname_records(
            client,
            zone_id,
            desired_records,
            ttl=args.ttl,
            proxied=args.proxied,
            delete_stale=args.delete_stale,
            dry_run=args.dry_run,
            domain_scope=domain_name,
        )

        if args.output == "json":
            print(
                json.dumps(
                    {
                        "domain": domain_name,
                        "zone_id": zone_id,
                        "create": plan["create"],
                        "update": plan["update"],
                        "delete": plan["delete"],
                    },
                    indent=2,
                )
            )
            return 0

        print(f"Domain: {domain_name}")
        print(f"Zone ID: {zone_id}")
        print(f"Create: {len(plan['create'])}")
        print(f"Update: {len(plan['update'])}")
        print(f"Delete: {len(plan['delete'])}")

        for operation in ("create", "update", "delete"):
            for record in plan[operation]:
                print(f"{operation.upper()}: {record['name']}")

        return 0
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
