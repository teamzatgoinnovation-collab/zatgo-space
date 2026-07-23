# Installation — ZatGo Space

## Development

1. Ensure ERPNext site exists (`./scripts/create_site.sh development <site>`).
2. `./scripts/install_custom_apps.sh development <site> zatgo_space`
3. Desk → reload (`bench clear-cache` if needed).

## Production

Include the app git URL in `ERPNEXT/production/apps.json` and build `CUSTOM_IMAGE`.
