"""Frappe hooks for ZatGo Space.

Keep invasive overrides rare and documented via ADR when introduced.
"""

app_name = "zatgo_space"
app_title = "ZatGo Space"
app_publisher = "ZatGo Innovation"
app_description = "Self-serve site provisioning for zatgo.online subdomains"
app_email = "engineering@zatgo.local"
app_license = "mit"
app_version = "0.1.0"

after_install = "zatgo_space.install.after_install"
after_migrate = "zatgo_space.install.after_migrate"
