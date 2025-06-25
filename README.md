# Skytap Python Client

This package provides a simple Python interface to the Skytap REST API.

## Installation

```sh
pip install https://github.com/gravitylens/skytap-python/releases/download/v0.1.1/cyberark_identity_library-0.1.1-py3-none-any.whl
```

## Setup

Create a `.env` file in your project directory with:
```
skytap_username=your_username
skytap_api_token=your_token
bitly_token=your_bitly_token
```

## Usage

```python
from skytap.skytap import SkytapClient

client = SkytapClient()
print(client.get_departments())
```

Create a `.env` file containing your Skytap `username` and `password`. You may
also include a `bitly_token` for URL shortening. Call `set_authorization()` to
load these credentials before using other methods. The `.env` file is parsed
using the `python-dotenv` package.

## Available Functions

The `SkytapClient` class implements the following methods:

- `log_write(message)`
- `show_request_failure(exc)`
- `show_web_request_failure(exc)`
- `set_authorization(env_file=None)`
- `add_configuration_to_project(config_id, project_id)`
- `copy_configuration(config_id, vm_ids=None)`
- `edit_configuration(config_id, attributes)`
- `edit_vm(config_id, vm_id, attributes)`
- `update_run_state(config_id, new_state, vm_id=None)`
- `get_projects(project_id=None)`
- `get_vms(config_id, vm_id=None)`
- `get_project_environments(project_id)`
- `add_network_adapter(config_id, vm_id, nic_type="default")`
- `edit_network_adapter(config_id, vm_id, interface_id, attributes)`
- `edit_vm_userdata(config_id, vm_id, contents)`
- `connect_network(source_network, destination_network)`
- `remove_network(tunnel_id)`
- `create_environment_from_template(template_id)`
- `create_project(name, description="")`
- `publish_url(config_id, publish_set_type="single_url", name=None, sso=False)`
- `save_configuration_to_template(config_id, vm_ids, networks="none", name="")`
- `remove_configuration(config_id)`
- `remove_template(template_id)`
- `remove_project(project_id)`
- `add_template_to_project(project_id, template_id)`
- `add_template_to_configuration(config_id, template_id)`
- `get_configurations(config_id=None)`
- `get_templates(template_id=None)`
- `get_vm_user_data(config_id, vm_id)`
- `get_published_urls(config_id)`
- `get_published_url_details(publish_set_id)`
- `get_published_services(config_id, vm_id, interface_id)`
- `get_department_quotas(department_id)`
- `get_departments(department_id=None)`
- `get_users(user_id=None)`
- `add_user(login_name, first_name, last_name, email, account_role="restricted_user", can_import=False, can_export=False, time_zone="Pacific Time (US & Canada)", region="US-West")`
- `add_group(group_name, description="")`
- `add_department(department_name, description="")`
- `add_environment_tag(config_id, tags)`
- `add_template_tag(template_id, tags)`
- `get_tags(config_id=None, template_id=None, asset_id=None)`
- `get_vm_credentials(vm_id)`
- `attach_wan(env_id, network_id, wan_id)`
- `connect_wan(env_id, network_id, wan_id)`
- `get_wan(wan_id)`
- `get_network(config_id, network_id)`
- `update_environment_userdata(config_id, userdata)`
- `rename_environment(config_id, new_name)`
- `update_auto_suspend(config_id, suspend_on_idle)`
- `add_user_to_project(project_id, user_id, project_role="participant")`
- `add_user_to_group(group_id, user_id)`
- `get_metadata()`
- `add_schedule(object_id, title, schedule_actions, start_at, *, stype="config", recurring_days=None, end_at=None, timezone="Pacific Time (US & Canada)", delete_at_end=False)`
- `get_usage(rid="0", start_at=None, end_at=None, resource="svms", region="all", agg="month", groupby="user", fmt="csv")`
- `get_audit_report(rid="0", start_at=None, end_at=None, activity="")`
- `get_public_ips()`
- `get_schedules(schedule_id=None)`
- `connect_public_ip(vm_id, interface_id, public_ip)`
- `publish_service(config_id, vm_id, interface_id, service_id, port)`
- `remove_tag(config_id, tag_id)`
- `get_bitly_url(long_url, token=None)`
- `get_share_password(length=6)`
- `update_sharing_portal_password(env_id, portal_id, share_pw)`
- `update_sharing_portal_access(env_id, access="run_and_use")`
- `new_sharing_portal(env_id, share_pw=None)`
- `new_session_environment(project_id, template_id, env_name, disable_power_options=False, project_name=None)`
- `new_session(session_name, template_id, environments_needed, *, spreadsheet_path=None, disable_power_options=False)`
- `remove_session(project_id)`
- `start_session(project_id, delay_between=0, delay_after=0)`
- `stop_session(project_id, delay_between=0, delay_after=0)`
- `status_session(project_id)`
- `replace_environment_with_template(env_id, template_id)`
- `remove_vm_from_environment(env_id, vm_id)`
- `get_unassigned_public_ips(region="")`
- `merge_arrays(array1, array2)`
- `edit_subnet(env_id, network_id, subnet_cidr)`
