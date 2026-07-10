# Estado del artefacto PDF — Gold B2B SaaS

## Resultado

El PDF fue generado correctamente después del commit `b8f0398`.

- HTML fuente: `outputs/gold/gold-b2b-saas/report_print.html`
- PDF generado: `outputs/gold/gold-b2b-saas/report.pdf`
- Tamaño: ~593 KB
- Extensión verificada: documento PDF, versión 1.4
- Páginas: 8
- Apertura local: verificada con `open outputs/gold/gold-b2b-saas/report.pdf`

## Qué ocurrió inicialmente

La generación vía WeasyPrint falló por una dependencia del sistema no disponible:

```text
OSError: cannot load library 'libgobject-2.0-0'
```

Esto no era un error del modelo ni del reporte HTML. Era un problema del backend local de conversión HTML→PDF.

## Solución aplicada

Se usó Google Chrome local en modo headless para imprimir el HTML preparado para impresión:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --no-sandbox \
  --print-to-pdf="outputs/gold/gold-b2b-saas/report.pdf" \
  "file://$PWD/outputs/gold/gold-b2b-saas/report_print.html"
```

## Lectura defendible

El sistema genera un reporte HTML estilizado y una versión `report_print.html` preparada para impresión. En este entorno, el PDF se obtuvo con un backend de navegador local. La falta inicial de PDF correspondía a una dependencia de sistema de WeasyPrint, no a falta de artefacto base.

## Limitación

`outputs/` está ignorado por Git. El PDF existe como artefacto local de ejecución, no como archivo versionado del repositorio.
