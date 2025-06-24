import base64
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import socket


import os
import time
import csv
import secrets



import requests
from dotenv import dotenv_values


class SkytapClient:
    """Simple Python client for the Skytap REST API."""

    def __init__(
        self,
        base_url: str = "https://cloud.skytap.com",
        logfile: str = "skytap.log",
        env_file: str = ".env",
        bitly_token: Optional[str] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers: Dict[str, str] = {"Accept": "application/json"}
        self.logfile = logfile
        self.env_file = env_file
        self.bitly_token = bitly_token

        # Load bitly_token from .env if not provided
        if bitly_token is None:
            creds = dotenv_values(self.env_file)
            self.bitly_token = creds.get("bitly_token")
        else:
            self.bitly_token = bitly_token

    def log_write(self, message: str) -> None:
        """Append a timestamped message to the configured log file."""
        ts = datetime.now().isoformat()
        with open(self.logfile, "a", encoding="utf-8") as fh:
            fh.write(f"{ts}  {message}\n")

    def show_request_failure(self, exc: Exception) -> Dict[str, Any]:
        """Return structured information about a failed request."""
        if isinstance(exc, requests.HTTPError):
            resp = exc.response
            return {
                "requestResultCode": resp.status_code if resp else -1,
                "eDescription": resp.reason if resp else str(exc),
                "eMessage": resp.text if resp else str(exc),
                "method": resp.request.method if resp and resp.request else "",
            }
        return {
            "requestResultCode": getattr(exc, "errno", -1),
            "eDescription": exc.__class__.__name__,
            "eMessage": str(exc),
            "method": "",
        }

    def show_web_request_failure(self, exc: Exception) -> Dict[str, Any]:
        """Simplified failure information used by the PowerShell module."""
        if isinstance(exc, requests.HTTPError) and exc.response is not None:
            return {
                "requestResultCode": exc.response.status_code,
                "eDescription": exc.response.reason,
            }
        return {
            "requestResultCode": -1,
            "eDescription": str(exc),
        }

    def set_authorization(self, env_file: Optional[str] = None) -> None:
        """Load credentials from a .env file."""
        path = Path(env_file or self.env_file)
        if not path.exists():
            raise FileNotFoundError(f"The .env file {path} was not found")
        creds = dotenv_values(path)
        user = creds.get("username")
        password = creds.get("password")
        bitly_token = creds.get("bitly_token")
        if user is None or password is None:
            raise ValueError("username and password must be provided in the .env file")
        token = base64.b64encode(f"{user}:{password}".encode("ascii")).decode("ascii")
        self.headers["Authorization"] = f"Basic {token}"
        if bitly_token:
            self.bitly_token = bitly_token

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        resp = requests.request(method, url, headers=self.headers, **kwargs)
        resp.raise_for_status()
        if resp.text:
            return resp.json()
        return None

    def add_configuration_to_project(self, config_id: str, project_id: str) -> Any:
        return self._request(
            "POST", f"/projects/{project_id}/configurations/{config_id}"
        )

    def copy_configuration(self, config_id: str, vm_ids: Optional[List[str]] = None) -> Any:
        body: Dict[str, Any] = {"configuration_id": config_id}
        if vm_ids:
            body["vm_ids"] = vm_ids
        return self._request("POST", "/configurations", json=body)

    def edit_configuration(self, config_id: str, attributes: Dict[str, Any]) -> Any:
        return self._request("PUT", f"/configurations/{config_id}", json=attributes)

    def edit_vm(self, config_id: str, vm_id: str, attributes: Dict[str, Any]) -> Any:
        return self._request(
            "PUT", f"/configurations/{config_id}/vms/{vm_id}/", json=attributes
        )

    def update_run_state(self, config_id: str, new_state: str, vm_id: Optional[str] = None) -> Any:
        path = f"/configurations/{config_id}"
        if vm_id:
            path += f"/vms/{vm_id}"
        body = {"runstate": new_state}
        return self._request("PUT", path, json=body)
    def get_projects(self, project_id: Optional[str] = None) -> Any:
        path = f"/projects/{project_id}" if project_id else "/projects"
        return self._request("GET", path)

    def get_vms(self, config_id: str, vm_id: Optional[str] = None) -> Any:
        path = f"/configurations/{config_id}/vms"
        if vm_id:
            path += f"/{vm_id}"
        return self._request("GET", path)

    def get_project_environments(self, project_id: str) -> Any:
        path = f"/projects/{project_id}/configurations"
        return self._request("GET", path)
    def add_network_adapter(self, config_id: str, vm_id: str, nic_type: str = "default") -> Any:
        body = {"nic_type": nic_type}
        return self._request("POST", f"/configurations/{config_id}/vms/{vm_id}/interfaces", json=body)

    def edit_network_adapter(self, config_id: str, vm_id: str, interface_id: str, attributes: Dict[str, Any]) -> Any:
        return self._request(
            "PUT",
            f"/configurations/{config_id}/vms/{vm_id}/interfaces/{interface_id}",
            json=attributes,
        )

    def edit_vm_userdata(self, config_id: str, vm_id: str, contents: str) -> Any:
        return self._request(
            "PUT",
            f"/configurations/{config_id}/vms/{vm_id}/user_data",
            json={"contents": contents},
        )

    def connect_network(self, source_network: str, destination_network: str) -> Any:
        body = {"source_network_id": source_network, "target_network_id": destination_network}
        return self._request("POST", "/tunnels", json=body)

    def remove_network(self, tunnel_id: str) -> Any:
        return self._request("DELETE", f"/tunnels/{tunnel_id}")

    def create_environment_from_template(self, template_id: str) -> Any:
        return self._request("POST", "/configurations", json={"template_id": template_id})

    def create_project(self, name: str, description: str = "") -> Any:
        return self._request("POST", "/projects", json={"name": name, "summary": description})

    def publish_url(
        self,
        config_id: str,
        publish_set_type: str = "single_url",
        name: Optional[str] = None,
        sso: bool = False,
    ) -> Any:
        if name is None:
            name = f"Published set - {publish_set_type}"
        body = {"name": name, "publish_set_type": publish_set_type}
        if sso:
            body["sso_required"] = True
        return self._request("POST", f"/configurations/{config_id}/publish_sets", json=body)

    def save_configuration_to_template(
        self,
        config_id: str,
        vm_ids: List[str],
        networks: str = "none",
        name: str = "",
    ) -> Any:
        body = {
            "configuration_id": config_id,
            "vm_ids": vm_ids,
            "network_option": networks,
            "template_name": name,
        }
        return self._request("POST", "/templates", json=body)

    def remove_configuration(self, config_id: str) -> Any:
        return self._request("DELETE", f"/configurations/{config_id}")

    def remove_template(self, template_id: str) -> Any:
        return self._request("DELETE", f"/templates/{template_id}")

    def remove_project(self, project_id: str) -> Any:
        return self._request("DELETE", f"/projects/{project_id}")

    def add_template_to_project(self, project_id: str, template_id: str) -> Any:
        return self._request("POST", f"/projects/{project_id}/templates/{template_id}")

    def add_template_to_configuration(self, config_id: str, template_id: str) -> Any:
        return self._request("POST", f"/configurations/{config_id}/templates/{template_id}")

    def get_configurations(self, config_id: Optional[str] = None) -> Any:
        path = f"/configurations/{config_id}" if config_id else "/configurations"
        return self._request("GET", path)

    def get_templates(self, template_id: Optional[str] = None) -> Any:
        path = f"/templates/{template_id}" if template_id else "/templates"
        return self._request("GET", path)

    def get_vm_user_data(self, config_id: str, vm_id: str) -> Any:
        return self._request("GET", f"/configurations/{config_id}/vms/{vm_id}/user_data")

    def get_published_urls(self, config_id: str) -> Any:
        return self._request("GET", f"/configurations/{config_id}/publish_sets")

    def get_published_url_details(self, publish_set_id: str) -> Any:
        return self._request("GET", f"/publish_sets/{publish_set_id}")

    def get_published_services(self, config_id: str, vm_id: str, interface_id: str) -> Any:
        path = f"/configurations/{config_id}/vms/{vm_id}/interfaces/{interface_id}/services"
        return self._request("GET", path)

    def get_department_quotas(self, department_id: str) -> Any:
        return self._request("GET", f"/departments/{department_id}/quotas")

    def get_departments(self, department_id: Optional[str] = None) -> Any:
        path = f"/departments/{department_id}" if department_id else "/departments"
        return self._request("GET", path)

    def get_users(self, user_id: Optional[str] = None) -> Any:
        path = f"/users/{user_id}" if user_id else "/users"
        return self._request("GET", path)

    def add_user(
        self,
        login_name: str,
        first_name: str,
        last_name: str,
        email: str,
        account_role: str = "restricted_user",
        can_import: bool = False,
        can_export: bool = False,
        time_zone: str = "Pacific Time (US & Canada)",
        region: str = "US-West",
    ) -> Any:
        body = {
            "login_name": login_name,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "account_role": account_role,
            "can_import": can_import,
            "can_export": can_export,
            "time_zone": time_zone,
            "region": region,
        }
        return self._request("POST", "/users", json=body)

    def add_group(self, group_name: str, description: str = "") -> Any:
        return self._request("POST", "/groups", json={"name": group_name, "description": description})

    def add_department(self, department_name: str, description: str = "") -> Any:
        return self._request("POST", "/departments", json={"name": department_name, "description": description})

    def add_environment_tag(self, config_id: str, tags: List[str]) -> Any:
        return self._request("POST", f"/configurations/{config_id}/tags", json={"tags": tags})

    def add_template_tag(self, template_id: str, tags: List[str]) -> Any:
        return self._request("POST", f"/templates/{template_id}/tags", json={"tags": tags})

    def get_tags(
        self,
        config_id: Optional[str] = None,
        template_id: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> Any:
        if config_id:
            return self._request("GET", f"/configurations/{config_id}/tags")
        if template_id:
            return self._request("GET", f"/templates/{template_id}/tags")
        if asset_id:
            return self._request("GET", f"/assets/{asset_id}/tags")
        return None

    def get_vm_credentials(self, vm_id: str) -> Any:
        return self._request("GET", f"/vms/{vm_id}/credentials")

    def attach_wan(self, env_id: str, network_id: str, wan_id: str) -> Any:
        return self._request(
            "POST",
            f"/configurations/{env_id}/networks/{network_id}/wans/{wan_id}",
        )

    def connect_wan(self, env_id: str, network_id: str, wan_id: str) -> Any:
        return self._request(
            "POST",
            f"/configurations/{env_id}/networks/{network_id}/wans/{wan_id}/connect",
        )

    def get_wan(self, wan_id: str) -> Any:
        return self._request("GET", f"/wans/{wan_id}")

    def get_network(self, config_id: str, network_id: str) -> Any:
        return self._request("GET", f"/configurations/{config_id}/networks/{network_id}")

    def update_environment_userdata(self, config_id: str, userdata: Dict[str, Any]) -> Any:
        return self._request(
            "PUT", f"/configurations/{config_id}/user_data", json=userdata
        )

    def rename_environment(self, config_id: str, new_name: str) -> Any:
        """Rename an environment."""
        body = {"name": new_name}
        return self._request("PUT", f"/configurations/{config_id}", json=body)

    def update_auto_suspend(self, config_id: str, suspend_on_idle: int) -> Any:
        """Set auto suspend timeout in seconds."""
        body = {"suspend_on_idle": suspend_on_idle}
        return self._request("PUT", f"/configurations/{config_id}", json=body)

    def add_user_to_project(
        self, project_id: str, user_id: str, project_role: str = "participant"
    ) -> Any:
        """Add a user to a project with the given role."""
        body = {"role": project_role}
        return self._request(
            "POST", f"/projects/{project_id}/users/{user_id}", json=body
        )

    def add_user_to_group(self, group_id: str, user_id: str) -> Any:
        """Add a user to a group."""
        return self._request(
            "POST", f"/groups/{group_id}/users/{user_id}", json={}
        )

    def get_metadata(self) -> Any:
        """Retrieve VM metadata from inside a Skytap VM."""
        host_ip = socket.gethostbyname(socket.gethostname())
        octets = host_ip.split(".")
        meta_ip = f"{octets[0]}.{octets[1]}.{octets[2]}.254"
        resp = requests.get(f"http://{meta_ip}/skytap")
        resp.raise_for_status()
        return resp.json()

    def add_schedule(
        self,
        object_id: str,
        title: str,
        schedule_actions: List[Dict[str, Any]],
        start_at: str,
        *,
        stype: str = "config",
        recurring_days: Optional[str] = None,
        end_at: Optional[str] = None,
        timezone: str = "Pacific Time (US & Canada)",
        delete_at_end: bool = False,
    ) -> Any:
        """Create a schedule for a configuration or template."""
        body: Dict[str, Any] = {
            "title": title,
            "start_at": start_at,
            "time_zone": timezone,
            "actions": schedule_actions,
        }
        if stype == "config":
            body["configuration_id"] = object_id
        else:
            body["template_id"] = object_id
        if end_at:
            body["end_at"] = end_at
        if recurring_days:
            body["recurring_days"] = recurring_days
        if delete_at_end:
            body["delete_at_end"] = True
        return self._request("POST", "/schedules", json=body)

    def get_usage(
        self,
        rid: str = "0",
        start_at: Optional[str] = None,
        end_at: Optional[str] = None,
        resource: str = "svms",
        region: str = "all",
        agg: str = "month",
        groupby: str = "user",
        fmt: str = "csv",
    ) -> Any:
        """Create or retrieve a usage report."""
        if rid == "0":
            body = {
                "start_date": start_at,
                "end_date": end_at,
                "resource_type": resource,
                "region": region,
                "group_by": groupby,
                "aggregate_by": agg,
                "results_format": fmt,
                "utc": True,
                "notify_by_email": False,
            }
            return self._request("POST", "/reports", json=body)
        result = self._request("GET", f"/reports/{rid}")
        if isinstance(result, dict) and result.get("ready"):
            return self._request("GET", f"/reports/{rid}.csv")
        return result

    def get_audit_report(
        self,
        rid: str = "0",
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
        activity: str = "",
    ) -> Any:
        """Create or retrieve an audit report."""
        if rid == "0":
            if not (start_at and end_at):
                raise ValueError("start_at and end_at are required for new report")
            body = {
                "date_start": {
                    "year": start_at.year,
                    "month": start_at.month,
                    "day": start_at.day,
                    "hour": start_at.hour,
                    "minute": start_at.minute,
                },
                "date_end": {
                    "year": end_at.year,
                    "month": end_at.month,
                    "day": end_at.day,
                    "hour": end_at.hour,
                    "minute": end_at.minute,
                },
                "activity": activity,
                "notify_by_email": False,
            }
            return self._request("POST", "/auditing/exports", json=body)
        result = self._request("GET", f"/auditing/exports/{rid}")
        if isinstance(result, dict) and result.get("ready"):
            return self._request("GET", f"/auditing/exports/{rid}.csv")
        return result

    def get_public_ips(self) -> Any:
        """Return the list of public IPs for the account."""
        return self._request("GET", "/ips")

    def get_schedules(self, schedule_id: Optional[str] = None) -> Any:
        path = f"/schedules/{schedule_id}" if schedule_id else "/schedules"
        return self._request("GET", path)

    def connect_public_ip(self, vm_id: str, interface_id: str, public_ip: str) -> Any:
        body = {"ip": public_ip}
        return self._request(
            "POST",
            f"/vms/{vm_id}/interfaces/{interface_id}/ips",
            json=body,
        )

    def publish_service(
        self,
        config_id: str,
        vm_id: str,
        interface_id: str,
        service_id: str,
        port: str,
    ) -> Any:
        body = {"port": port}
        return self._request(
            "POST",
            f"/configurations/{config_id}/vms/{vm_id}/interfaces/{interface_id}/services/{service_id}",
            json=body,
        )

    def remove_tag(self, config_id: str, tag_id: str) -> Any:
        if tag_id.lower() == "all":
            tags = self.get_tags(config_id=config_id) or []
            results = []
            for tag in tags:
                tid = tag.get("id") if isinstance(tag, dict) else tag
                try:
                    results.append(
                        self._request(
                            "DELETE",
                            f"/configurations/{config_id}/tags/{tid}",
                        )
                    )
                except requests.HTTPError:
                    results.append(None)
            return results
        return self._request(
            "DELETE", f"/configurations/{config_id}/tags/{tag_id}"
        )


    def get_bitly_url(self, long_url: str) -> str:
        """Return a Bitly shortened URL.

        Requires the bitly_token to be set on the client.
        If the request fails, the original ``long_url`` is returned.
        """
        token = self.bitly_token
        if not token:
            raise ValueError("Bitly token is not set on the client")

    def get_bitly_url(self, long_url: str) -> str:
        """Return a Bitly shortened URL.

        Requires the ``BITLY_AUTH_TOKEN`` environment variable to be set.
        If the request fails, the original ``long_url`` is returned.
        """
        token = os.getenv("BITLY_AUTH_TOKEN")
        if not token:
            raise ValueError("BITLY_AUTH_TOKEN environment variable not set")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        body = {"domain": "bit.ly", "long_url": long_url}
        try:
            resp = requests.post(
                "https://api-ssl.bitly.com/v4/shorten",
                headers=headers,
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("link", long_url)
        except Exception:
            return long_url

    def get_bitly_url(self, long_url: str, token: Optional[str] = None) -> str:
        """Return a Bitly shortened URL or the original on failure."""
        auth = token or self.bitly_token
        if not auth:
            return long_url
        headers = {"Authorization": f"Bearer {auth}", "Content-Type": "application/json"}
        body = {"domain": "bit.ly", "long_url": long_url}
        try:
            resp = requests.post("https://api-ssl.bitly.com/v4/shorten", headers=headers, json=body)
            resp.raise_for_status()
            return resp.json().get("link", long_url)
        except Exception:
            return long_url

    def get_share_password(self, length: int = 6) -> str:
        """Generate a random share password."""
        chars = "ABCDEFGHJKMNOPQRSTUVWXYZ"
        return "".join(secrets.choice(chars) for _ in range(length))

    def update_sharing_portal_password(self, env_id: str, portal_id: str, share_pw: str) -> Any:
        body = {"password": share_pw}
        return self._request(
            "PUT", f"/configurations/{env_id}/publish_sets/{portal_id}", json=body
        )

    def update_sharing_portal_access(self, env_id: str, access: str = "run_and_use") -> List[Any]:
        vms = self.get_vms(env_id) or []
        vm_list = [
            {"vm_ref": f"https://cloud.skytap.com/vms/{vm['id']}", "access": access}
            for vm in vms
            if isinstance(vm, dict)
        ]
        body = {"vms": vm_list}
        results = []
        portals = self.get_published_urls(env_id) or []
        for portal in portals:
            pid = portal.get("id") if isinstance(portal, dict) else portal
            results.append(
                self._request(
                    "PUT",
                    f"/configurations/{env_id}/publish_sets/{pid}",
                    json=body,
                )
            )
        return results

    def new_sharing_portal(self, env_id: str, share_pw: Optional[str] = None) -> Dict[str, Any]:
        env = self.get_configurations(env_id)
        name = env.get("name", "Published set - single_url") if isinstance(env, dict) else None
        portal = self.publish_url(env_id, name=name)
        long_url = portal.get("desktops_url") if isinstance(portal, dict) else None
        self.update_sharing_portal_access(env_id)
        if share_pw:
            self.update_sharing_portal_password(env_id, portal.get("id"), share_pw)
        short_url = self.get_bitly_url(long_url) if long_url else None
        return {"LongURL": long_url, "ShortURL": short_url, "SharePassword": share_pw}

    def new_session_environment(
        self,
        project_id: str,
        template_id: str,
        env_name: str,
        disable_power_options: bool = False,
        project_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        env = self.create_environment_from_template(template_id)
        env = self.rename_environment(env["id"], env_name)
        if disable_power_options:
            self.edit_configuration(env["id"], {"suspend_on_idle": "", "shutdown_on_idle": ""})
        self.add_configuration_to_project(env["id"], project_id)
        portal = self.new_sharing_portal(env["id"], self.get_share_password())
        while True:
            cfg = self.get_configurations(env["id"])
            if not isinstance(cfg, dict) or cfg.get("runstate") != "busy":
                break
            time.sleep(5)
        return {
            "Session": project_name,
            "Id": env["id"],
            "Environment": env_name,
            "LongURL": portal.get("LongURL"),
            "ShortURL": portal.get("ShortURL"),
            "Password": portal.get("SharePassword"),
        }

    def new_session(
        self,
        session_name: str,
        template_id: str,
        environments_needed: int,
        *,
        spreadsheet_path: Optional[str] = None,
        disable_power_options: bool = False,
    ) -> Dict[str, Any]:
        if spreadsheet_path:
            with open(spreadsheet_path, "r", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            names = [f"{session_name}({row.get('email','')})" for row in rows]
            environments_needed = len(names)
        else:
            names = [f"{session_name}({i:03})" for i in range(environments_needed)]
            rows = [{} for _ in range(environments_needed)]
        project = self.create_project(session_name)
        self.add_template_to_project(project["id"], template_id)
        envs = []
        for i in range(environments_needed):
            env = self.new_session_environment(
                project["id"],
                template_id,
                names[i],
                disable_power_options=disable_power_options,
                project_name=project.get("name"),
            )
            envs.append({**env, **rows[i]})
        return {
            "ProjectID": project["id"],
            "SessionName": project.get("name"),
            "TemplateUsed": template_id,
            "Environments": envs,
        }

    def remove_session(self, project_id: str) -> None:
        envs = self.get_project_environments(project_id) or []
        for env in envs:
            self.remove_configuration(env.get("id"))
        self.remove_project(project_id)

    def start_session(self, project_id: str, delay_between: int = 0, delay_after: int = 0) -> None:
        for env in self.get_project_environments(project_id) or []:
            self.update_run_state(env.get("id"), "running")
            if delay_between:
                time.sleep(delay_between)
        if delay_after:
            time.sleep(delay_after)

    def stop_session(self, project_id: str, delay_between: int = 0, delay_after: int = 0) -> None:
        for env in self.get_project_environments(project_id) or []:
            self.update_run_state(env.get("id"), "stopped")
            if delay_between:
                time.sleep(delay_between)
        if delay_after:
            time.sleep(delay_after)

    def status_session(self, project_id: str) -> Dict[str, Any]:
        project = self.get_projects(project_id)
        report = {
            "SessionName": project.get("name") if isinstance(project, dict) else "",
            "TotalEnvironments": 0,
            "RunningEnvironments": 0,
        }
        env_reports = []
        for env in self.get_project_environments(project_id) or []:
            env_report = {
                "EnvironmentName": env.get("name"),
                "StoppedVMs": 0,
                "RunningVMs": 0,
                "BusyVMs": 0,
                "RateLimited": False,
            }
            vms = self.get_vms(env.get("id")) or []
            for vm in vms:
                env_report["RateLimited"] = env_report["RateLimited"] or vm.get("rate_limited", False)
                state = vm.get("runstate", "")
                if state.startswith("running"):
                    env_report["RunningVMs"] += 1
                elif state.startswith("busy"):
                    env_report["BusyVMs"] += 1
                elif state.startswith("stopped") or state.startswith("suspended"):
                    env_report["StoppedVMs"] += 1
            if env_report["RunningVMs"] == len(vms):
                report["RunningEnvironments"] += 1
            report["TotalEnvironments"] += 1
            env_reports.append(env_report)
        return {"report": report, "environments": env_reports}

    def replace_environment_with_template(self, env_id: str, template_id: str) -> None:
        vms = self.get_vms(env_id) or []
        for vm in vms:
            self.remove_vm_from_environment(env_id, vm.get("id"))
        self.add_template_to_configuration(env_id, template_id)
        self.update_sharing_portal_access(env_id)

    def remove_vm_from_environment(self, env_id: str, vm_id: str) -> Any:
        return self._request("DELETE", f"/configurations/{env_id}/vms/{vm_id}")

    def get_unassigned_public_ips(self, region: str = "") -> List[Any]:
        ips = self.get_public_ips() or []
        result = [ip for ip in ips if isinstance(ip, dict) and (ip.get("nics") == [] or ip.get("nics", []) == [])]
        if region:
            result = [ip for ip in result if ip.get("region") == region]
        return result

    def merge_arrays(
        self, array1: List[Dict[str, Any]], array2: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if len(array1) != len(array2):
            raise ValueError("Arrays are Unequal Length")
        return [{**a, **b} for a, b in zip(array1, array2)]

    def edit_subnet(self, env_id: str, network_id: str, subnet_cidr: str) -> Any:
        body = {"subnet": subnet_cidr}
        return self._request(
            "PUT", f"/configurations/{env_id}/networks/{network_id}", json=body
        )

