$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

docker compose -f infra/local/docker-compose.yml up -d
$env:PETI_ENVIRONMENT = 'LOCAL'
$env:PETI_AUTH_MODE = 'LOCAL_TEST'
$env:PETI_STORAGE_MODE = 'FIRESTORE_EMULATOR'
$env:PETI_FIRESTORE_EMULATOR_HOST = '127.0.0.1:4588'
$env:STORAGE_EMULATOR_HOST = 'http://127.0.0.1:4588'

@'
import sys
sys.path.insert(0, "backend")
from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    a = {"Authorization": "Bearer local-test:floci-user-a"}
    b = {"Authorization": "Bearer local-test:floci-user-b"}
    assert client.get("/v1/me", headers=a).status_code == 200
    created = client.post("/v1/pets", headers={**a, "Idempotency-Key": "floci-smoke-1"}, json={"species": "DOG", "display_name": "Floci"})
    assert created.status_code == 201
    pet = created.json()
    retry = client.post("/v1/pets", headers={**a, "Idempotency-Key": "floci-smoke-1"}, json={"species": "DOG", "display_name": "Floci"})
    assert retry.status_code == 201 and retry.json()["id"] == pet["id"]
    assert client.get("/v1/pets", headers=b).json() == []
    assert client.patch(f"/v1/pets/{pet['id']}", headers=a, json={"display_name": "Floci renamed"}).status_code == 200
    assert client.delete(f"/v1/pets/{pet['id']}", headers=a).status_code == 204
print("Floci integration smoke passed")
'@ | python -
