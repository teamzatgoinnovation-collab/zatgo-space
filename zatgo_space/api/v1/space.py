"""Public / provisioner APIs for ZatGo Space."""

from __future__ import annotations

import json
import re
from typing import Any

import frappe
from frappe import _

from zatgo_space.api.response import fail, ok

DOMAIN_SUFFIX = "zatgo.online"
SLUG_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")
RESERVED = {
	"www",
	"erp",
	"space",
	"bench",
	"api",
	"mail",
	"ftp",
	"ns1",
	"ns2",
	"cdn",
	"admin",
	"status",
	"docs",
	"app",
	"apps",
	"portal",
}

DEFAULT_APPS = [
	{"package": "frappe", "title": "Frappe Framework", "required": True},
	{"package": "erpnext", "title": "ERPNext", "required": False},
	{"package": "hrms", "title": "HRMS", "required": False},
]


def _parse_features(raw: str | None) -> list[str]:
	if not raw:
		return []
	try:
		data = json.loads(raw)
		if isinstance(data, list):
			return [str(x) for x in data]
	except Exception:
		pass
	return [line.strip() for line in raw.splitlines() if line.strip()]


def _assert_internal_token():
	expected = frappe.conf.get("space_internal_token") or ""
	provided = frappe.get_request_header("X-Space-Token") or frappe.form_dict.get("token") or ""
	if not expected or provided != expected:
		frappe.throw(_("Invalid space internal token"), frappe.PermissionError)


@frappe.whitelist(allow_guest=True)
def list_catalog():
	"""Plans + installable app catalog for the Space wizard."""
	plans = []
	if frappe.db.exists("DocType", "Space Plan"):
		rows = frappe.get_all(
			"Space Plan",
			filters={"is_active": 1},
			fields=["code", "title", "mock_price", "features", "sort_order"],
			order_by="sort_order asc",
		)
		for row in rows:
			plans.append(
				{
					"code": row.code,
					"title": row.title,
					"mock_price": row.mock_price,
					"features": _parse_features(row.features),
				}
			)
	else:
		from zatgo_space.install import MOCK_PLANS

		for p in MOCK_PLANS:
			plans.append(
				{
					"code": p["code"],
					"title": p["title"],
					"mock_price": p["mock_price"],
					"features": p["features"],
				}
			)

	suffix = frappe.conf.get("space_domain_suffix") or DOMAIN_SUFFIX
	return ok(
		{
			"domainSuffix": suffix,
			"apps": DEFAULT_APPS,
			"plans": plans,
			"inviteRequired": bool(frappe.conf.get("space_invite_code")),
		}
	)


@frappe.whitelist(allow_guest=True)
def create_order(
	slug: str,
	plan: str,
	apps: str | list | None = None,
	payment_method: str = "Mock",
	invite_code: str | None = None,
):
	"""Create a Draft Space Order (no admin password stored)."""
	expected_invite = frappe.conf.get("space_invite_code") or ""
	if expected_invite and (invite_code or "") != expected_invite:
		return fail("INVITE_REQUIRED", "Valid invite code required")

	slug = (slug or "").strip().lower()
	if not SLUG_RE.match(slug):
		return fail("INVALID_SLUG", "Invalid subdomain slug")
	if slug in RESERVED:
		return fail("RESERVED_SLUG", f"Subdomain '{slug}' is reserved")

	suffix = frappe.conf.get("space_domain_suffix") or DOMAIN_SUFFIX
	hostname = f"{slug}.{suffix}"

	if frappe.db.exists("Space Order", {"hostname": hostname, "status": ["in", ["Draft", "Provisioning", "Active"]]}):
		return fail("HOSTNAME_TAKEN", f"Hostname already ordered: {hostname}")

	if not frappe.db.exists("Space Plan", plan):
		return fail("INVALID_PLAN", f"Unknown plan: {plan}")

	app_list: list[Any] = []
	if isinstance(apps, str):
		try:
			app_list = json.loads(apps)
		except Exception:
			app_list = [a.strip() for a in apps.split(",") if a.strip()]
	elif isinstance(apps, list):
		app_list = apps

	packages = []
	for item in app_list:
		if isinstance(item, dict):
			pkg = item.get("package") or item.get("app_package")
			title = item.get("title") or pkg
		else:
			pkg = str(item)
			title = pkg
		if not pkg or not re.match(r"^[a-z][a-z0-9_]*$", pkg):
			continue
		packages.append({"app_package": pkg, "title": title})

	if not any(p["app_package"] == "frappe" for p in packages):
		packages.insert(0, {"app_package": "frappe", "title": "Frappe Framework"})

	doc = frappe.get_doc(
		{
			"doctype": "Space Order",
			"slug": slug,
			"hostname": hostname,
			"plan": plan,
			"payment_method": payment_method if payment_method in ("Mock", "Stripe", "PayPal") else "Mock",
			"status": "Draft",
			"desk_url": f"https://{hostname}",
			"apps": packages,
		}
	)
	# Guest may create draft orders for the public wizard.
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	return ok(
		{
			"name": doc.name,
			"slug": doc.slug,
			"hostname": doc.hostname,
			"status": doc.status,
			"deskUrl": doc.desk_url,
			"plan": doc.plan,
			"apps": [{"package": r.app_package, "title": r.title} for r in doc.apps],
		}
	)


@frappe.whitelist(allow_guest=True)
def get_order(name: str | None = None, job_id: str | None = None):
	"""Fetch order status for the wizard."""
	filters = {}
	if name:
		filters["name"] = name
	elif job_id:
		filters["job_id"] = job_id
	else:
		return fail("MISSING_ID", "name or job_id required")

	if not frappe.db.exists("Space Order", filters):
		return fail("NOT_FOUND", "Space Order not found")

	doc = frappe.get_doc("Space Order", filters)
	logs = []
	if frappe.db.exists("DocType", "Space Job Log"):
		logs = frappe.get_all(
			"Space Job Log",
			filters={"order": doc.name},
			fields=["stage", "status", "message", "creation"],
			order_by="creation asc",
			limit_page_length=100,
		)

	return ok(
		{
			"name": doc.name,
			"slug": doc.slug,
			"hostname": doc.hostname,
			"status": doc.status,
			"deskUrl": doc.desk_url,
			"plan": doc.plan,
			"jobId": doc.job_id,
			"error": doc.error_message,
			"apps": [{"package": r.app_package, "title": r.title} for r in doc.apps],
			"logs": logs,
		}
	)


@frappe.whitelist()
def update_order_status(
	name: str,
	status: str,
	job_id: str | None = None,
	error_message: str | None = None,
	admin_password_set: int | None = None,
	stage: str | None = None,
	stage_status: str | None = None,
	message: str | None = None,
	log_text: str | None = None,
):
	"""Provisioner callback — requires X-Space-Token matching site_config space_internal_token."""
	_assert_internal_token()

	if status not in ("Draft", "Provisioning", "Active", "Failed"):
		return fail("INVALID_STATUS", status)

	doc = frappe.get_doc("Space Order", name)
	doc.status = status
	if job_id:
		doc.job_id = job_id
	if error_message is not None:
		doc.error_message = error_message
	if admin_password_set is not None:
		doc.admin_password_set = 1 if admin_password_set else 0
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)

	if stage:
		frappe.get_doc(
			{
				"doctype": "Space Job Log",
				"order": doc.name,
				"job_id": job_id or doc.job_id or "unknown",
				"stage": stage,
				"status": stage_status or "running",
				"message": message,
				"log_text": log_text,
			}
		).insert(ignore_permissions=True)

	frappe.db.commit()
	return ok({"name": doc.name, "status": doc.status})
