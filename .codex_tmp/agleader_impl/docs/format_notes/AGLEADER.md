# Ag Leader AGDATA / ILF2: primer hito experimental

## Muestra

`2026-07-21_05-45-05.agdata`, generado por `AL INTEGRA 7.8.0`.

Solo se dispone de una exportaciÃ³n. Conforme a `AGENTS.md`, el lector no se
considera validado y no asigna significado agronÃ³mico a canales desconocidos.

## Estructura confirmada

1. Firma ASCII `AG LEADER TECHNOLOGY` en el byte 0.
2. Cabecera de colecciÃ³n de 400 bytes en la muestra.
3. TAR POSIX localizado mediante el marcador `ustar`.
4. 83 miembros: 71 `.ilf2`, 8 `.iby2`, 3 `.objects` y 1 `.pat2`.
5. Cada ILF2 observado tiene 272 bytes de cabecera y un flujo DEFLATE crudo.
6. El flujo contiene registros con marcador, longitud, tipo y carga Ãºtil.

## Registro GPS confirmado en la muestra

GUID binario: `b463d1b9cbb2bd47b6d4fec1894ba6a5`.

| Offset | Tipo | InterpretaciÃ³n |
|---:|---|---|
| 16 | uint64 LE | milisegundos Unix UTC |
| 32 | float64 LE | longitud WGS84 |
| 40 | float64 LE | latitud WGS84 |
| 48 | float64 LE | altitud, hipÃ³tesis fuerte de metros |

La trayectoria observada se sitÃºa aproximadamente en `(-3.89, 42.41)` y las
fechas corresponden a julio de 2026, coherentes con la exportaciÃ³n.

## Sensores sin semÃ¡ntica confirmada

GUID: `a3edeee7ee0bdf45a550a11c7fc6d664`. Contiene dos vectores `float64`.
Se exportan como `sensor_01..sensor_N`; no se asignan a rendimiento, humedad,
velocidad o anchura porque una serie plausible no es evidencia suficiente.

## Pendiente

- Exportar el mismo trabajo desde Ag Leader SMS con todos los atributos.
- Relacionar por fecha, trayectoria y orden de registro.
- Determinar nombre, unidad, escala y estado de cada canal.
- Validar con una segunda exportaciÃ³n independiente de Ag Leader.
