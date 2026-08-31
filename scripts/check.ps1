$ErrorActionPreference = 'Stop'
$repo = Resolve-Path (Join-Path $PSScriptRoot '..')
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw 'Python 3.13 is required; install it before running the release gate.' }
$env:PYTHONPATH = Join-Path $repo 'backend'
& $python.Source -c "import app.main; import app.main_worker"
if ($LASTEXITCODE -ne 0) { throw 'Backend import smoke test failed.' }
& $python.Source -m compileall -q (Join-Path $repo 'backend/app')
if ($LASTEXITCODE -ne 0) { throw 'Backend compilation failed.' }
& $python.Source -m pytest (Join-Path $repo 'backend/tests/test_agent_execution.py') (Join-Path $repo 'backend/tests/test_agent_queue.py') (Join-Path $repo 'backend/tests/test_google_ssv.py') -q
if ($LASTEXITCODE -ne 0) { throw 'Focused backend tests failed.' }
Write-Output 'PETi release gate: PASS'
