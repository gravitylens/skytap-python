import os
import sys
import types
import json
import base64

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Provide a minimal requests stub when the real library is unavailable
try:
    import requests  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - environment without requests
    requests = types.SimpleNamespace()

    class Response:
        def __init__(self):
            self.status_code = 200
            self.reason = "OK"
            self.text = ""
            self._content = b""
            self.url = ""
            self.headers = {}
            self.request = None

        def json(self):
            if self._content:
                return json.loads(self._content.decode())
            if self.text:
                return json.loads(self.text)
            return {}

        def raise_for_status(self):
            if self.status_code >= 400:
                raise HTTPError(response=self)

    class HTTPError(Exception):
        def __init__(self, response=None):
            super().__init__()
            self.response = response

    class Request:
        def __init__(self, method, url):
            self.method = method
            self.url = url

        def prepare(self):
            return self

    def request(method, url, headers=None, **kwargs):
        resp = Response()
        resp.url = url
        return resp

    def post(url, **kwargs):
        return request("POST", url, **kwargs)

    def get(url, **kwargs):
        return request("GET", url, **kwargs)

    requests.Response = Response
    requests.HTTPError = HTTPError
    requests.Request = Request
    requests.request = request
    requests.post = post
    requests.get = get
    sys.modules['requests'] = requests

from skytap.skytap import SkytapClient


def make_response(status=200, content=b"{}"):
    resp = requests.Response()
    resp.status_code = status
    resp._content = content
    resp.url = "http://example.com"
    return resp


def test_set_authorization(tmp_path):
    env = tmp_path / ".env"
    env.write_text("username=foo\npassword=bar")
    client = SkytapClient(env_file=str(env))
    client.set_authorization()
    token = base64.b64encode(b"foo:bar").decode("ascii")
    assert client.headers["Authorization"] == f"Basic {token}"


def test_get_users(monkeypatch, capsys):
    client = SkytapClient()

    def fake_request(method, path, **kwargs):
        assert method == "GET" and path == "/users"
        return [{"id": "u1"}]

    monkeypatch.setattr(client, "_request", fake_request)
    result = client.get_users()
    print(result)
    captured = capsys.readouterr()
    assert "u1" in captured.out


def test_get_departments(monkeypatch, capsys):
    client = SkytapClient()

    def fake_request(method, path, **kwargs):
        assert method == "GET" and path == "/departments"
        return [{"id": "d1"}]

    monkeypatch.setattr(client, "_request", fake_request)
    result = client.get_departments()
    print(result)
    captured = capsys.readouterr()
    assert "d1" in captured.out


def test_get_public_ips(monkeypatch, capsys):
    client = SkytapClient()

    def fake_request(method, path, **kwargs):
        assert method == "GET" and path == "/ips"
        return ["1.2.3.4"]

    monkeypatch.setattr(client, "_request", fake_request)
    result = client.get_public_ips()
    print(result)
    captured = capsys.readouterr()
    assert "1.2.3.4" in captured.out


def test_get_bitly_url(monkeypatch, capsys):
    client = SkytapClient()

    class Resp(requests.Response):
        pass

    fake_response = Resp()
    fake_response._content = json.dumps({"link": "https://bit.ly/abc"}).encode()

    def fake_post(url, headers=None, json=None):
        assert url.startswith("https://api-ssl.bitly.com")
        return fake_response

    monkeypatch.setenv("BITLY_AUTH_TOKEN", "token")
    monkeypatch.setattr(requests, "post", fake_post)
    result = client.get_bitly_url("https://www.google.com")
    print(result)
    captured = capsys.readouterr()
    assert "bit.ly/abc" in captured.out
