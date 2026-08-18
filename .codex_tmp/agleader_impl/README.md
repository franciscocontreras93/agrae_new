# EXPORTAR_RINDES_FORMATOS

Conversor extensible de mapas de rendimiento a un modelo geoespacial común.

## Estado

- CNH: detección, inventario y lectores experimentales documentados.
- CLAAS: detección de directorios ISOXML y extracción auditable de coordenadas de
  archivos `.CM`. Las muestras actuales no declaran rendimiento ni humedad.
- TOPCON: lectura de registros ISOXML TLG y exportación GeoPackage.
- AG LEADER: primer hito experimental AGDATA/ILF2; exporta recorrido, fecha,
  altitud y canales crudos. Rendimiento y humedad aÃºn no estÃ¡n identificados.
- Salidas previstas: GeoPackage (principal), Shapefile, CSV y GeoJSON.

## Ubicación recomendada en Windows

`D:\Mi unidad\EXPORTAR_RINDES_FORMATOS`

## Puesta en marcha

En PowerShell, desde la raíz del proyecto:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup_windows.ps1
```

Ejemplos:

```powershell
python -m exportar_rindes inspect "data\raw\CNH\250805L6.cn1.zip"
python -m exportar_rindes inspect "CLASS\TASKDATA_EXPORT_TASKDATA 2024.08.14_13_41"
python -m exportar_rindes convert `
  "CLASS\TASKDATA_EXPORT_TASKDATA 2024.08.14_13_41" `
  --output "outputs\claas_tracks.gpkg"
pytest
```

## Principios del proyecto

1. No modificar nunca los datos originales.
2. Mantener un lector independiente por fabricante.
3. Convertir todos los formatos al modelo común definido en `core/models.py`.
4. Exportar primero a GeoPackage; generar SHP únicamente por compatibilidad.
5. Registrar trazabilidad, advertencias y filtros aplicados.

Consulta `AGENTS.md` antes de pedir cambios a Codex.
