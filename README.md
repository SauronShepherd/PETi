# PETi

PETi es una aplicación web responsive de cuidado responsable para mascotas. Permite organizar perfiles, registrar observaciones, analizar imágenes, audio y vídeo con asistencia cloud, consultar historial, gestionar documentos veterinarios y recibir recordatorios de cuidados.

La experiencia está diseñada como un producto gratuito, privado y centrado en el bienestar. Los resultados son orientativos y no sustituyen la valoración de un profesional veterinario.

## Inicio rápido

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e backend[dev]
./scripts/check
./scripts/run-backend
```

En Windows: `scripts\\bootstrap.cmd`, `scripts\\check.cmd` y `scripts\\run-backend.ps1`.

El backend expone `GET /health/live` y `GET /health/ready`. La verificación local no requiere credenciales de producción ni servicios cloud de pago.

## Verificación

```text
python -m ruff check backend
python -m pytest -q
```

Para la aplicación, consulta [`web/README.md`](web/README.md). El gate principal verifica backend y cliente web.

La aplicación usa Firebase para identidad y notificaciones cuando se configura un entorno real; las credenciales y configuraciones sensibles se suministran externamente y no deben almacenarse en el repositorio.

## Documentación

- [Arquitectura](docs/HACKATHON_ARCHITECTURE.md)
- [Auditoría final de preparación para el hackathon](docs/FINAL_HACKATHON_READINESS_AUDIT_2026-08-29.md)
- [Guion de demostración](docs/HACKATHON_DEMO_SCRIPT.md)
- [Instrucciones de pruebas](docs/HACKATHON_TESTING_INSTRUCTIONS.md)
- [Privacidad y seguridad](docs/ARCHITECTURE_INVARIANTS.md)
- [Materiales de release](release/)
