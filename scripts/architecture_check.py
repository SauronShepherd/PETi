from pathlib import Path
root=Path(__file__).resolve().parents[1]
android=root/'android'
generated = {'build', '.gradle', '.gradle-home', '__pycache__', '.git', '.terraform', '.mypy_cache', '.pytest_cache', '.ruff_cache', '.idea'}
for path in android.rglob('*') if android.exists() else []:
    if generated.intersection(path.parts):
        continue
    if path.is_file() and path.suffix in {'.kt','.kts','.properties','.xml'}:
        text=path.read_text(errors='ignore').lower()
        assert 'gemini' not in text, f'Gemini reference in Android: {path}'
        assert 'com.google.ai.' not in text, f'Google AI SDK reference in Android: {path}'
        assert 'generativeai' not in text, f'Generative AI SDK reference in Android: {path}'
        assert 'firebase.firestore' not in text, f'Direct Firestore client in Android: {path}'
        relative = path.relative_to(android).as_posix().lower()
        if path.suffix == '.kt' and 'com.google.android.gms.ads' in text:
            assert '/funding/' in f'/{relative}', f'Advertising dependency/API outside funding: {path}'
        if path.suffix == '.kt' and 'httpurlconnection' in text.lower() and 'setRequestProperty("Accept"' in text:
            assert 'x-correlation-id' in text.lower(), f'HTTP adapter missing X-Correlation-ID: {path}'
        if 'import com.peti.app.funding.rewardedadgateway' in text and '/funding/' not in f'/{relative}':
            raise AssertionError(f'RewardedAdGateway outside funding: {path}')
scan_roots = [root / name for name in ('backend', 'android', 'contracts', 'infra', 'eval', 'scripts')]
for scan_root in scan_roots:
  for path in scan_root.rglob('*') if scan_root.exists() else []:
    if path.is_file() and path.name not in {'.gitignore'} and 'node_modules' not in path.parts and not generated.intersection(path.parts):
        if path.suffix.lower() not in {'.py', '.kt', '.kts', '.xml', '.json', '.yaml', '.yml', '.md', '.toml', '.ps1', '.properties'}:
            continue
        text=path.read_text(errors='ignore')
        marker = 'AI' + 'za'
        # Firebase's generated google-services.json necessarily contains a
        # client-side API key. It is not a secret credential; private service
        # account keys must never be shipped in the Android app.
        if path.name != 'google-services.json':
            assert marker not in text, f'Possible credential: {path}'
        if path.parts[:2] == (root.name, 'android') and path.name in {'build.gradle.kts', 'build.gradle', 'libs.versions.toml'}:
            lowered = text.lower()
            for forbidden in ('tflite', 'litert', 'tensorflow', 'com.google.ai.', 'generativeai'):
                assert forbidden not in lowered, f'Local AI dependency in Android: {path}'
print('Architecture and secret checks passed')
