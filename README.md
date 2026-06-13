# Secret Reader

A Home Assistant custom integration that exposes a service to read values from
`secrets.yaml` at runtime — for use in automations and scripts.

---

> [!WARNING]
> **Security Warning**
>
> This integration reads values from `secrets.yaml` at **runtime** and returns them
> as a service response. This is a **deliberate bypass** of the HA security model,
> which intentionally only uses `secrets.yaml` values at configuration time and never
> exposes them via the API.
>
> **What this means:**
> - Values from `secrets.yaml` will appear in **automation traces** and **log entries**.
> - Any user with service access can — if misconfigured — read **all** secrets.
> - The user restriction only protects against **interactive UI/API calls**.
>   Automations run without a user context and are **always allowed**.
>
> Only install this if you are aware of the consequences.
> For encrypted secrets with explicit opt-in →
> [ha-secret-entities](https://github.com/Big-Gremlin/ha-secret-entities).

---

## Installation

### HACS (recommended)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Big-Gremlin&repository=ha-secret-reader&category=integration)

1. HACS → Integrations → ⋮ → *Custom repositories*
2. Add the repository URL, category *Integration*
3. Install *Secret Reader* and restart Home Assistant

### Manual

Copy `custom_components/secret_reader/` into the `config/custom_components/` folder of your Home Assistant instance and restart HA.

## Setup

*Settings* → *Devices & Services* → *Add integration* → **Secret Reader**. Select allowed users via *Configure* (options).

## How it works

- The integration registers the `secret_reader.read` service.
- In the **options** you can define which HA users are allowed to call the service.
- An empty list means: all users allowed.
- Automations (no user context) are **always** allowed, regardless of the list.

## Service: `secret_reader.read`

```yaml
action: secret_reader.read
data:
  name: my_api_key
response_variable: result
# result.name  → "my_api_key"
# result.value → the value from secrets.yaml
```

Example in an automation:

```yaml
- action: secret_reader.read
  data:
    name: pushover_token
  response_variable: secret
- action: notify.pushover
  data:
    message: "Hello"
    data:
      token: "{{ secret.value }}"
```

The service throws an error if `secrets.yaml` does not exist, the key is not found,
or the calling user is not on the allowlist.

## Development

```bash
pip install -r requirements_test.txt
pytest
```

## License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

This project uses the MIT License, for more details see the [license document](LICENSE).

---

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/biggremlin)
