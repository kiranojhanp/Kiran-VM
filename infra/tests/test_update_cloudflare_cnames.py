from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
import unittest
from unittest import mock


SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "scripts"
    / "update_cloudflare_cnames.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "update_cloudflare_cnames", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load update_cloudflare_cnames module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class UpdateCloudflareCnamesTests(unittest.TestCase):
    def test_reads_domain_and_labels_from_taskfile(self):
        module = load_module()
        taskfile_content = """
vars:
  DOMAIN_NAME_DEFAULT: example.com
  DNS_SUBDOMAIN_LABELS: backup,git,n8n
  CLOUDFLARE_ZONE_ID_DEFAULT: zone-id-123
"""

        config = module.parse_taskfile_defaults(taskfile_content)

        self.assertEqual(config.domain_name, "example.com")
        self.assertEqual(config.subdomain_labels, ["backup", "git", "n8n"])
        self.assertEqual(config.cloudflare_zone_id, "zone-id-123")

    def test_computes_create_update_and_delete_actions(self):
        module = load_module()

        desired = module.build_desired_cname_records(
            domain_name="example.com",
            subdomain_labels=["backup", "git"],
        )
        existing = [
            {
                "id": "rec-backup",
                "name": "backup.example.com",
                "type": "CNAME",
                "content": "old.example.com",
                "ttl": 1,
                "proxied": False,
            },
            {
                "id": "rec-stale",
                "name": "stale.example.com",
                "type": "CNAME",
                "content": "example.com",
                "ttl": 1,
                "proxied": False,
            },
        ]

        plan = module.plan_cname_changes(
            desired_records=desired,
            existing_records=existing,
            ttl=1,
            proxied=False,
            delete_stale=True,
        )

        self.assertEqual(len(plan["create"]), 1)
        self.assertEqual(plan["create"][0]["name"], "git.example.com")
        self.assertEqual(len(plan["update"]), 1)
        self.assertEqual(plan["update"][0]["id"], "rec-backup")
        self.assertEqual(len(plan["delete"]), 1)
        self.assertEqual(plan["delete"][0]["id"], "rec-stale")

    def test_cloudflare_client_uses_sdk_dns_records_api(self):
        module = load_module()

        class FakeRecordsApi:
            def __init__(self):
                self.calls = []

            def list(self, **kwargs):
                self.calls.append(("list", kwargs))
                return {
                    "result": [
                        {
                            "id": "rec-1",
                            "name": "backup.example.com",
                            "type": "CNAME",
                            "content": "example.com",
                            "ttl": 1,
                            "proxied": False,
                        }
                    ],
                    "result_info": {"total_pages": 1},
                }

            def create(self, **kwargs):
                self.calls.append(("create", kwargs))

            def update(self, dns_record_id, **kwargs):
                self.calls.append(("update", dns_record_id, kwargs))

            def delete(self, dns_record_id, **kwargs):
                self.calls.append(("delete", dns_record_id, kwargs))

        class FakeDnsApi:
            def __init__(self):
                self.records = FakeRecordsApi()

        class FakeCloudflareSdk:
            def __init__(self):
                self.dns = FakeDnsApi()

        fake_sdk = FakeCloudflareSdk()
        client = module.CloudflareClient(api_token="token", sdk_client=fake_sdk)

        listed = client.list_cname_records("zone-1")
        client.create_dns_record(
            "zone-1",
            {
                "name": "git.example.com",
                "type": "CNAME",
                "content": "example.com",
                "ttl": 1,
                "proxied": False,
            },
        )
        client.update_dns_record(
            "zone-1",
            "rec-1",
            {
                "name": "backup.example.com",
                "type": "CNAME",
                "content": "example.com",
                "ttl": 1,
                "proxied": False,
            },
        )
        client.delete_dns_record("zone-1", "rec-2")

        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["id"], "rec-1")
        self.assertEqual(fake_sdk.dns.records.calls[0][0], "list")
        self.assertEqual(fake_sdk.dns.records.calls[1][0], "create")
        self.assertEqual(fake_sdk.dns.records.calls[2][0], "update")
        self.assertEqual(fake_sdk.dns.records.calls[3][0], "delete")

    def test_delete_stale_scopes_to_target_domain_only(self):
        module = load_module()

        desired = module.build_desired_cname_records(
            domain_name="example.com",
            subdomain_labels=["backup"],
        )
        existing = [
            {
                "id": "rec-external",
                "name": "legacy.other.com",
                "type": "CNAME",
                "content": "other.com",
                "ttl": 1,
                "proxied": False,
            },
            {
                "id": "rec-stale",
                "name": "git.example.com",
                "type": "CNAME",
                "content": "example.com",
                "ttl": 1,
                "proxied": False,
            },
        ]

        plan = module.plan_cname_changes(
            desired_records=desired,
            existing_records=existing,
            ttl=1,
            proxied=False,
            delete_stale=True,
            domain_scope="example.com",
        )

        self.assertEqual(len(plan["delete"]), 1)
        self.assertEqual(plan["delete"][0]["id"], "rec-stale")

    def test_validates_domain_and_labels_before_sync(self):
        module = load_module()

        with self.assertRaises(ValueError):
            module.validate_dns_inputs("example.com", ["bad label"])

    def test_resolve_api_token_prompts_in_interactive_mode(self):
        module = load_module()

        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(module.sys.stdin, "isatty", return_value=True):
                with mock.patch("getpass.getpass", return_value="token-from-prompt"):
                    token = module.resolve_api_token(None)

        self.assertEqual(token, "token-from-prompt")

    def test_resolve_api_token_fails_non_interactive_without_token(self):
        module = load_module()

        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(module.sys.stdin, "isatty", return_value=False):
                with self.assertRaises(ValueError):
                    module.resolve_api_token(None)

    def test_resolve_cloudflare_auth_accepts_api_key_and_email(self):
        module = load_module()

        with mock.patch.dict(
            os.environ,
            {"CF_API_KEY": "api-key-1", "CF_API_EMAIL": "me@example.com"},
            clear=True,
        ):
            auth = module.resolve_cloudflare_auth(None, None, None)

        self.assertEqual(auth["api_key"], "api-key-1")
        self.assertEqual(auth["api_email"], "me@example.com")

    def test_resolve_cloudflare_auth_rejects_api_key_without_email(self):
        module = load_module()

        with mock.patch.dict(os.environ, {"CF_API_KEY": "api-key-1"}, clear=True):
            with self.assertRaises(ValueError):
                module.resolve_cloudflare_auth(None, None, None)


if __name__ == "__main__":
    unittest.main()
