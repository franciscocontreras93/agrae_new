# Guía de estilos del mapa de rendimiento

## 1. Qué representan los estilos

Los 42 elementos disponibles en **Propiedades de la capa > Estilos** no son
capas diferentes. Son distintas formas de representar la misma retícula de la
capa maestra `00_ANALISIS_GENERAL`.

Cada estilo colorea las celdas utilizando un campo diferente. Se emplean tres
tipos principales de clasificación:

- **Por cultivo:** calcula rangos independientes para cada cultivo. Evita
  comparar directamente, por ejemplo, trigo y remolacha con los mismos límites.
- **Divergente:** representa diferencias alrededor de `0` o cumplimientos
  alrededor de `100 %`.
- **Índice global:** utiliza rangos fijos y comparables, con `100 %` como valor
  de referencia.

---

## 2. Rendimientos

### 01. Rendimiento ajustado por cultivo

Rendimiento final utilizado en el análisis, expresado en `kg/ha`.

Parte del dato de la cosechadora y puede incorporar:

- eliminación de registros inválidos;
- corrección por humedad de referencia;
- ajuste mediante producción real de báscula, si se proporciona;
- limitación de valores superiores anómalos validada en el histograma.

Los colores se calculan de manera independiente para cada cultivo. Es el estilo
principal para representar el resultado final.

### 02. Rendimiento bruto por cultivo

Rendimiento original del sensor convertido de `t/ha` a `kg/ha`, antes del
ajuste final.

Se utiliza para comprobar la información original, estudiar la calibración del
sensor y comparar el mapa de entrada con el corregido.

### 03. Diferencia de rendimiento

```text
Diferencia = rendimiento ajustado − producción esperada
```

Unidad: `kg/ha`.

- Valor negativo: producción inferior a la esperada.
- Valor próximo a cero: coincidencia con el objetivo.
- Valor positivo: producción superior a la esperada.

### 04. Cumplimiento del objetivo

```text
Cumplimiento (%) = 100 × rendimiento ajustado / producción esperada
```

- `100 %`: cumplimiento exacto.
- `80 %`: se alcanzó el 80 % de lo esperado.
- `120 %`: se produjo un 20 % más de lo esperado.
- `NULL`: no existe una producción esperada válida o es igual a cero.

---

## 3. Biomasa, residuo y materia seca

### 05. Biomasa por cultivo

Estimación de la biomasa aérea total:

```text
Biomasa = rendimiento / índice de cosecha
```

El índice de cosecha expresa qué proporción de la biomasa total corresponde al
producto cosechado.

### 06. Residuo por cultivo

Parte de la biomasa que no se retira como cosecha:

```text
Residuo = biomasa − rendimiento
```

Puede representar paja, tallos, hojas y otros restos, según el cultivo.

### 07. Materia seca de cosecha por cultivo

```text
Materia seca cosecha = rendimiento × fracción de materia seca de la cosecha
```

### 08. Materia seca de residuo por cultivo

```text
Materia seca residuo = residuo × fracción de materia seca del residuo
```

La materia seca se utiliza como base para estimar las extracciones de
nutrientes.

---

## 4. Extracciones del cultivo

### 09. N extraído por cultivo

```text
N extraído =
materia seca cosecha × coeficiente N cosecha
+ materia seca residuo × coeficiente N residuo
```

Unidad: `kg N/ha`.

### 10. P extraído por cultivo

Mismo procedimiento para el fósforo. Unidad: `kg P/ha`.

### 11. K extraído por cultivo

Mismo procedimiento para el potasio. Unidad: `kg K/ha`.

Las extracciones se representan por cultivo porque sus valores habituales
dependen de la especie, el rendimiento y la composición de cosecha y residuo.

---

## 5. Fertilización propuesta en el mapa SIG

Los aportes propuestos proceden de las fórmulas y dosis del mapa SIG:

```text
f_fondo × d_fondo
f_cob1  × d_cob1
f_cob2  × d_cob2
f_cob3  × d_cob3
```

Para cada fertilizante, el script interpreta la fórmula N-P-K y multiplica su
proporción por la dosis prevista.

### 12. N propuesto

Nitrógeno total previsto en el plan: `kg N/ha`.

### 13. P propuesto

Fósforo total previsto en el plan: `kg P/ha`.

### 14. K propuesto

Potasio total previsto en el plan: `kg K/ha`.

---

## 6. Balances aparentes

Los balances comparan lo aplicado realmente según la hoja `OUT` con la
extracción estimada del cultivo.

### 15. Balance N

```text
Balance N = N aplicado − N extraído
```

### 16. Balance P

```text
Balance P = P aplicado − P extraído
```

### 17. Balance K

```text
Balance K = K aplicado − K extraído
```

Interpretación general:

- Negativo: extracción estimada superior al aporte.
- Cero: aporte y extracción aproximadamente equivalentes.
- Positivo: aporte superior a la extracción estimada.

> **Precaución:** estos balances no representan por sí solos el balance total
> del suelo. No incorporan necesariamente reservas, mineralización, fijación,
> lixiviación, volatilización, inmovilización ni aportes no registrados.

---

## 7. Eficiencia aparente de nutrientes

### 18. NUE por cultivo

```text
NUE = rendimiento / N aplicado
```

Unidad: `kg de cosecha por kg de N aplicado`.

### 19. PUE por cultivo

```text
PUE = rendimiento / P aplicado
```

### 20. KUE por cultivo

```text
KUE = rendimiento / K aplicado
```

Un valor elevado significa mucha producción por unidad aplicada, pero no
implica automáticamente una situación agronómicamente mejor. También puede
reflejar aportes bajos, utilización de reservas del suelo o información
incompleta. Por ello se representan con rangos independientes por cultivo.

---

## 8. Cobertura y control de valores extremos

### 21. Cobertura

Estimación de la superficie de cada celda respaldada por el recorrido del
sensor:

```text
Cobertura (%) ≈
100 × suma(distancia recorrida × ancho de corte) / área útil de la celda
```

- Cobertura baja: pocos datos para representar la celda.
- Próxima a `100 %`: cobertura espacial adecuada.
- Superior a `100 %`: posibles recorridos solapados o doble contabilización.

No representa cobertura vegetal. Es la cobertura espacial estimada de los
registros de la cosechadora.

### 22. Rendimiento antes del corte por cultivo

Rendimiento después de las correcciones iniciales, pero antes de limitar los
valores superiores anómalos con el histograma.

### 23. Límite superior

Valor máximo de rendimiento permitido en el lote después de validar el
histograma. Se expresa en `kg/ha`.

El límite se propone automáticamente y puede modificarse con el deslizador.

### 24. Exceso recortado

```text
Exceso = rendimiento antes del corte − límite superior
```

Solo presenta valor cuando el rendimiento previo supera el límite. Los
rendimientos bajos no se recortan.

Ejemplo:

```text
Rendimiento previo: 14.000 kg/ha
Límite superior:     10.500 kg/ha
Exceso recortado:     3.500 kg/ha
Rendimiento final:   10.500 kg/ha
```

---

## 9. Fertilización aplicada según la hoja OUT

El script lee siempre la hoja `OUT` y considera únicamente:

```text
f_aporte1 / aporte1
f_aporte2 / aporte2
f_aporte3 / aporte3
f_aporte4 / aporte4
```

Los aportes 5–7 y `nec_final` se ignoran intencionadamente.

### 25. N aplicado OUT

Nitrógeno total aplicado según los cuatro primeros aportes: `kg N/ha`.

### 26. P aplicado OUT

Fósforo total aplicado: `kg P/ha`.

### 27. K aplicado OUT

Potasio total aplicado: `kg K/ha`.

Si una unidad del mapa SIG no encuentra el mismo `IDDATA` en `OUT`, los campos
aplicados quedan como `NULL`.

---

## 10. Diferencia entre aplicación y propuesta

### 28. Diferencia N aplicado-propuesto

```text
Diferencia N = N aplicado OUT − N propuesto
```

### 29. Diferencia P aplicado-propuesto

```text
Diferencia P = P aplicado OUT − P propuesto
```

### 30. Diferencia K aplicado-propuesto

```text
Diferencia K = K aplicado OUT − K propuesto
```

En los tres casos:

- Negativo: se aplicó menos de lo propuesto.
- Cero: se respetó el plan.
- Positivo: se aplicó más de lo propuesto.

### 31. Diferencia porcentual N

```text
100 × (N aplicado − N propuesto) / N propuesto
```

### 32. Diferencia porcentual P

```text
100 × (P aplicado − P propuesto) / P propuesto
```

### 33. Diferencia porcentual K

```text
100 × (K aplicado − K propuesto) / K propuesto
```

Ejemplos:

- `−20 %`: se aplicó un 20 % menos.
- `0 %`: aplicación igual a la propuesta.
- `+15 %`: se aplicó un 15 % más.

---

## 11. Índices globales

Los estilos globales utilizan siempre la misma referencia:

| Índice | Clase | Interpretación |
|---:|---|---|
| `< 70 %` | Muy inferior | Muy por debajo de la referencia |
| `70–90 %` | Inferior | Por debajo de la referencia |
| `90–110 %` | Próximo | Cercano a la referencia |
| `110–130 %` | Superior | Por encima de la referencia |
| `> 130 %` | Muy superior | Muy por encima de la referencia |

### 34. Índice global de rendimiento

```text
100 × rendimiento ajustado / producción esperada
```

Permite comparar el comportamiento relativo de distintos cultivos y unidades.

### 35. Índice global de rendimiento bruto

```text
100 × rendimiento bruto / producción esperada
```

Muestra el comportamiento relativo del sensor antes del ajuste definitivo.

### 36. Índice global previo al corte

```text
100 × rendimiento anterior al corte / producción esperada
```

Permite comprobar la influencia de los valores extremos antes de limitarlos.

### 37. Índice N aplicado-propuesto

```text
100 × N aplicado / N propuesto
```

### 38. Índice P aplicado-propuesto

```text
100 × P aplicado / P propuesto
```

### 39. Índice K aplicado-propuesto

```text
100 × K aplicado / K propuesto
```

Para los estilos 37–39:

- `100 %`: se aplicó exactamente lo propuesto.
- `80 %`: se aplicó el 80 % de lo propuesto.
- `120 %`: se aplicó un 20 % más de lo propuesto.

---

## 12. Cobertura aparente de las extracciones

### 40. Cobertura aparente de extracción N

```text
100 × N aplicado / N extraído
```

### 41. Cobertura aparente de extracción P

```text
100 × P aplicado / P extraído
```

### 42. Cobertura aparente de extracción K

```text
100 × K aplicado / K extraído
```

Interpretación general:

- Menor de `100 %`: aporte inferior a la extracción estimada.
- Próximo a `100 %`: aporte parecido a la extracción estimada.
- Mayor de `100 %`: aporte superior a la extracción estimada.

Se denominan coberturas **aparentes** porque no incluyen todos los procesos del
suelo. Un valor de `100 %` no constituye automáticamente una recomendación
agronómica correcta.

---

## 13. Selección recomendada de estilos

### Para mostrar al agricultor

- `01 Rendimiento ajustado por cultivo`
- `03 Diferencia de rendimiento`
- `04 Cumplimiento del objetivo`
- `09–11 Extracciones N, P y K`
- `25–27 Nutrientes aplicados según OUT`
- `28–30 Diferencias aplicado-propuesto`
- `34 Índice global de rendimiento`
- `37–39 Índices aplicado-propuesto`

### Para control interno y auditoría

- `02 Rendimiento bruto por cultivo`
- `21 Cobertura`
- `22 Rendimiento antes del corte`
- `23 Límite superior`
- `24 Exceso recortado`
- `35 Índice global de rendimiento bruto`
- `36 Índice global previo al corte`

### Para interpretación agronómica con contexto adicional

- `15–17 Balances N, P y K`
- `18–20 NUE, PUE y KUE`
- `40–42 Coberturas aparentes de extracción`

Estos últimos indicadores deben interpretarse junto con información de suelo,
antecedentes, aportes orgánicos, mineralización, reservas y pérdidas de
nutrientes.

---

## 14. Resumen rápido de fórmulas

| Grupo | Fórmula básica |
|---|---|
| Diferencia de rendimiento | `rinde ajustado − producción esperada` |
| Cumplimiento/índice de rendimiento | `100 × rinde / producción esperada` |
| Biomasa | `rinde / índice de cosecha` |
| Residuo | `biomasa − rinde` |
| Balance nutricional | `aplicado − extraído` |
| NUE/PUE/KUE | `rinde / nutriente aplicado` |
| Diferencia aplicado-propuesto | `aplicado − propuesto` |
| Diferencia porcentual | `100 × (aplicado − propuesto) / propuesto` |
| Índice aplicado-propuesto | `100 × aplicado / propuesto` |
| Cobertura aparente de extracción | `100 × aplicado / extraído` |

## 15. Nota metodológica

El resultado sigue siendo una estimación espacial basada en los registros de la
cosechadora, los parámetros de cultivo, el mapa SIG y la fertilización declarada
en `OUT`. Cuando no existe producción confirmada de báscula, el rendimiento
ajustado no debe presentarse como un pesaje real exacto.
