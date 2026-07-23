# ZatGo Space

ERPNext custom application (`zatgo_space`) — control-plane DocTypes and APIs for **ZatGo Space** self-serve site provisioning on `*.zatgo.online`.

## Docs

- [Architecture](docs/architecture.md)
- [Installation](docs/installation.md)
- [API](docs/api.md)
- [Developer Guide](docs/developer.md)
- [Deployment](docs/deployment.md)
- [User Manual](docs/user_manual.md)
- [Changelog](docs/CHANGELOG.md)

## DocTypes

| DocType | Role |
|---------|------|
| Space Plan | Mock billing plans (Basic / Pro / Enterprise) |
| Space Order | Customer site order + status |
| Space Order App | Child table of selected apps |
| Space Job Log | Provisioning stage log |

## APIs (`zatgo_space.api.v1.space.*`)

- `list_catalog` (guest) — plans + apps
- `create_order` (guest) — draft order
- `get_order` (guest) — status poll
- `update_order_status` — provisioner callback (requires `X-Space-Token` = `space_internal_token` in site_config)

## Site config keys

```json
{
  "space_domain_suffix": "zatgo.online",
  "space_internal_token": "<random>"
}
```

## Install (DigitalOcean)

```bash
# on droplet backend container
bench get-app https://github.com/teamzatgoinnovation-collab/zatgo-space.git
bench --site erp.zatgo.online install-app zatgo_space
bench --site erp.zatgo.online migrate
bench --site erp.zatgo.online clear-cache
```

## Module nesting note

DocTypes live under `zatgo_space/zatgo_space/doctype/...` because `modules.txt` scrubs to the same name as the app package.
