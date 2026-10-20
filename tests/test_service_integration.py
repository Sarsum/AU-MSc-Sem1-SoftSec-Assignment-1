"""Black-box functional and authorization tests for the three services."""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


ROOT = Path(__file__).resolve().parents[1]
SERVICES = ROOT / "application"


def unused_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def services(tmp_path):
    private_key = Ed25519PrivateKey.generate()
    private_path = tmp_path / "private.pem"
    public_path = tmp_path / "public.pem"
    private_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_path.write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    api_port, resource_port, export_port = (unused_port() for _ in range(3))
    api_url = f"http://127.0.0.1:{api_port}"
    resource_url = f"http://127.0.0.1:{resource_port}"
    export_url = f"http://127.0.0.1:{export_port}"
    environment = os.environ.copy()
    processes = []
    for name, port in (
        ("resource", resource_port),
        ("export", export_port),
        ("api", api_port),
    ):
        service_dir = SERVICES / name
        service_workdir = tmp_path / name
        service_workdir.mkdir()
        service_environment = environment.copy()
        service_environment.update(
            {
                "JWT_PRIVKEY_FILE": str(private_path),
                "JWT_PUBKEY_FILE": str(public_path),
                "RESOURCES_BASE_URL": resource_url,
                "EXPORT_BASE_URL": export_url,
                "PYTHONPATH": os.pathsep.join(
                    [str(service_dir), str(ROOT / "dependency")]
                ),
            }
        )
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=service_workdir,
            env=service_environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        processes.append(process)

    urls = [api_url, resource_url, export_url]
    try:
        for url in urls:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if any(process.poll() is not None for process in processes):
                    pytest.fail("A service exited before it became ready")
                try:
                    if requests.get(f"{url}/openapi.json", timeout=1).ok:
                        break
                except requests.RequestException:
                    time.sleep(0.2)
            else:
                pytest.fail(f"Service did not start at {url}")
        yield api_url
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def register_and_login(api_url: str, username: str, role: str = "user") -> str:
    response = requests.post(
        f"{api_url}/register",
        json={"username": username, "password": "correct horse battery", "role": role},
        timeout=5,
    )
    assert response.status_code == 200, response.text
    response = requests.post(
        f"{api_url}/login",
        json={"username": username, "password": "correct horse battery"},
        timeout=5,
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_functional_and_authorization_flow(services):
    api_url = services
    user_token = register_and_login(api_url, "ci-user")
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Public account creation/login work and authenticated bucket/transaction
    # operations complete across the API and resource services.
    response = requests.post(
        f"{api_url}/bucket",
        json={"bucket_name": "groceries"},
        headers=user_headers,
        timeout=5,
    )
    assert response.status_code == 200, response.text
    response = requests.post(
        f"{api_url}/transaction",
        json={"bucket_name": "groceries", "amount": "12.50"},
        headers=user_headers,
        timeout=5,
    )
    assert response.status_code == 200, response.text

    # An unauthenticated request is denied, and a non-admin cannot reassign a bucket.
    response = requests.post(
        f"{api_url}/bucket", json={"bucket_name": "blocked"}, timeout=5
    )
    assert response.status_code == 401
    response = requests.post(
        f"{api_url}/bucket/groceries/reassign",
        json={"new_user_id": 99},
        headers=user_headers,
        timeout=5,
    )
    assert response.status_code == 403, response.text

    # A different user's token cannot read the first user's bucket's transactions.
    other_token = register_and_login(api_url, "ci-other-user")
    response = requests.get(
        f"{api_url}/bucket/groceries/transactions",
        headers={"Authorization": f"Bearer {other_token}"},
        timeout=5,
    )
    assert response.status_code == 404, response.text

    # Export traverses the export service and can then be downloaded by its owner.
    response = requests.post(
        f"{api_url}/bucket/groceries/export",
        headers=user_headers,
        timeout=10,
    )
    assert response.status_code == 200, response.text
    deadline = time.monotonic() + 10
    while True:
        response = requests.get(
            f"{api_url}/exports",
            params={"bucket_name": "groceries"},
            headers=user_headers,
            timeout=5,
        )
        if response.status_code == 200 or time.monotonic() >= deadline:
            break
        time.sleep(0.2)
    assert response.status_code == 200, response.text
    assert "12.5" in response.text
