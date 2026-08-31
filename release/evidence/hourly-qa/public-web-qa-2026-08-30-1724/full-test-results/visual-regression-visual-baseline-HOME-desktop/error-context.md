# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: visual-regression.spec.js >> visual baseline HOME
- Location: tests\e2e\visual-regression.spec.js:8:7

# Error details

```
Test timeout of 30000ms exceeded.
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - generic [ref=e5]:
      - generic [ref=e6]: ✤
      - text: PETi
    - generic [ref=e7]:
      - generic [ref=e8]: google-demo@example.test
      - generic [ref=e9]: G
      - button "Biblioteca" [ref=e10] [cursor=pointer]
      - button "Plan" [ref=e11] [cursor=pointer]
      - button "Compartir" [ref=e12] [cursor=pointer]
      - button "Ayuda" [ref=e13] [cursor=pointer]
      - button "Ajustes" [ref=e14] [cursor=pointer]
      - button "Admin" [ref=e15] [cursor=pointer]
      - button "Salir" [ref=e16] [cursor=pointer]
  - generic [ref=e17]:
    - complementary [ref=e18]:
      - navigation [ref=e19]:
        - button "⌂ Inicio" [ref=e20] [cursor=pointer]:
          - generic [ref=e21]: ⌂
          - text: Inicio
        - button "✦ Analizar" [ref=e22] [cursor=pointer]:
          - generic [ref=e23]: ✦
          - text: Analizar
        - button "◷ Historial" [ref=e24] [cursor=pointer]:
          - generic [ref=e25]: ◷
          - text: Historial
        - button "♙ Perfil" [ref=e26] [cursor=pointer]:
          - generic [ref=e27]: ♙
          - text: Perfil
        - button "✤ Agentes" [ref=e28] [cursor=pointer]:
          - generic [ref=e29]: ✤
          - text: Agentes
    - main [ref=e30]:
      - generic [ref=e31]:
        - generic [ref=e32]:
          - generic [ref=e33]:
            - strong [ref=e34]: Demo PETi
            - generic [ref=e35]: Selecciona una mascota para probar sus evidencias.
          - generic [ref=e36]: 2 mascotas
        - generic [ref=e37]:
          - button "Luna Luna Golden retriever · Sana" [ref=e38] [cursor=pointer]:
            - img "Luna" [ref=e39]
            - generic [ref=e40]:
              - text: Luna
              - generic [ref=e41]: Golden retriever · Sana
          - button "Max Max Border collie · Observación" [ref=e42] [cursor=pointer]:
            - img "Max" [ref=e43]
            - generic [ref=e44]:
              - text: Max
              - generic [ref=e45]: Border collie · Observación
        - generic [ref=e46]:
          - generic [ref=e47]: "Evidencias de Luna:"
          - button [ref=e48] [cursor=pointer]:
            - img "Evidencia 1 de Luna" [ref=e49]
          - button [ref=e50] [cursor=pointer]:
            - img "Evidencia 2 de Luna" [ref=e51]
          - button [ref=e52] [cursor=pointer]:
            - img "Evidencia 3 de Luna" [ref=e53]
          - button [ref=e54] [cursor=pointer]:
            - img "Evidencia 4 de Luna" [ref=e55]
          - button [ref=e56] [cursor=pointer]:
            - img "Evidencia 5 de Luna" [ref=e57]
      - generic [ref=e58]: Resumen diario
      - heading "Todo lo importante, hoy." [level=1] [ref=e59]
      - paragraph [ref=e60]: Información clara para cuidar mejor a tu mascota.
      - generic [ref=e61]:
        - generic [ref=e62]:
          - generic [ref=e63]: ✤
          - generic [ref=e64]:
            - heading "Luna" [level=2] [ref=e65]
            - generic [ref=e66]: DOG · Perfil registrado
          - generic [ref=e67]: Activo
        - generic [ref=e68]:
          - text: ♡
          - strong [ref=e69]: Sin datos
          - generic [ref=e70]: Salud general
        - generic [ref=e71]:
          - text: ◌
          - strong [ref=e72]: Sin datos
          - generic [ref=e73]: Actividad
        - generic [ref=e74]:
          - text: ◉
          - strong [ref=e75]: Sin datos
          - generic [ref=e76]: Cuidados
        - generic [ref=e77]:
          - heading "Mejor siguiente paso" [level=2] [ref=e78]
          - paragraph [ref=e79]: Registra una observación o analiza una evidencia para construir un resumen basado en datos reales.
          - generic [ref=e80]:
            - button "Analizar ahora" [ref=e81] [cursor=pointer]
            - button "Ver historial" [ref=e82] [cursor=pointer]
        - generic [ref=e83]:
          - heading "Estado" [level=2] [ref=e84]
          - generic [ref=e85]:
            - strong [ref=e86]: Información honesta
            - text: Las métricas aparecen cuando existen observaciones guardadas.
```