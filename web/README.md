# PETi Web

Web responsive de PETi, con el mismo lenguaje visual de las referencias y
conexión al backend Cloud API. La autenticación usa Firebase Web Auth:
email/contraseña y Google. La configuración se inyecta en runtime mediante
`window.PETI_CONFIG` y nunca se guarda en el repositorio.

## Ejecución local

Desde PowerShell, la forma recomendada es:

```powershell
.\scripts\start-web.ps1
```

También puede arrancarse manualmente:

```powershell
python -m http.server 4173 --bind 0.0.0.0 -d web
```

Abrir `http://localhost:4173/?demo=1` para la demo visual. Para habilitar autenticación real, definir antes
de cargar `index.html` un `window.PETI_CONFIG` con `apiBaseUrl` y
`firebaseConfig`, o reemplazar `web/config.example.js` por una configuración
local no versionada.

La página funciona sin backend para inspección visual con `?demo=1`, pero no
inventa datos: los estados vacíos se muestran como tales. Sin ese parámetro y
sin Firebase configurado, el acceso permanece cerrado.
