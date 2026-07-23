"""Install / migrate hooks for ZatGo Space."""

from __future__ import annotations

import json

import frappe

MOCK_PLANS = [
	{
		"code": "basic",
		"title": "Basic",
		"mock_price": "$0 / mo (mock)",
		"sort_order": 1,
		"features": ["1 site", "ERPNext core", "Community support"],
	},
	{
		"code": "pro",
		"title": "Pro",
		"mock_price": "$49 / mo (mock)",
		"sort_order": 2,
		"features": ["1 site", "ERPNext + HRMS", "Priority email support"],
	},
	{
		"code": "enterprise",
		"title": "Enterprise",
		"mock_price": "$199 / mo (mock)",
		"sort_order": 3,
		"features": ["Multi-site ready", "Custom apps", "Dedicated onboarding"],
	},
]


def after_install():
	seed_plans()


def after_migrate():
	seed_plans()


def seed_plans():
	for plan in MOCK_PLANS:
		if frappe.db.exists("Space Plan", plan["code"]):
			doc = frappe.get_doc("Space Plan", plan["code"])
			doc.title = plan["title"]
			doc.mock_price = plan["mock_price"]
			doc.sort_order = plan["sort_order"]
			doc.is_active = 1
			doc.features = json.dumps(plan["features"])
			doc.save(ignore_permissions=True)
		else:
			frappe.get_doc(
				{
					"doctype": "Space Plan",
					"code": plan["code"],
					"title": plan["title"],
					"mock_price": plan["mock_price"],
					"sort_order": plan["sort_order"],
					"is_active": 1,
					"features": json.dumps(plan["features"]),
				}
			).insert(ignore_permissions=True)
	frappe.db.commit()
