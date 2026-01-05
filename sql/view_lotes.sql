WITH base AS (
  SELECT DISTINCT
    d.iddata AS id,
    d.iddata,
    d.idcampania,
    d.idexplotacion,
    c.nombre AS campania,
    exp.nombre AS explotacion,
    l.idlote,
    d.idcultivo,
    d.idregimen,
    l.nombre AS lote,
    cult.nombre AS cultivo,
    d.prod_esperada::int,
    reg.nombre AS regimen,
    d.fertilizantefondoformula AS formulafondo,
    d.fertilizantecob1formula AS formulacob1,
    d.fertilizantecob2formula AS formulacob2,
    d.fertilizantecob3formula AS formulacob3,
    d.fechasiembra::date AS fechasiembra,
    d.fechacosecha,
    d.prod_final,
    round((st_area(st_transform(l.geom,8857)) / 10000)::numeric,2) AS area_ha,
    l.geom
  FROM agrae.lotes l
  JOIN campaign.data d ON d.idlote = l.idlote
  JOIN campaign.campanias c ON d.idcampania = c.id
  JOIN agrae.explotacion exp ON exp.idexplotacion = d.idexplotacion
  LEFT JOIN agrae.cultivo cult ON d.idcultivo = cult.idcultivo
  LEFT JOIN analytic.regimen reg ON reg.id = d.idregimen
  WHERE d.idcampania = {} AND d.idexplotacion = {}
),
params AS (
  SELECT
    0.0065::double precision AS lapse_c_per_m,
    15::int AS years_back,     -- 👈 parámetro
    365::int AS max_days_forward                     -- horizonte futuro para predicción
),
lote_pt AS (
  SELECT
    b.*,
    l.elev AS l_elev,
    ST_PointOnSurface(b.geom) AS pt,
    c.temp_base::double precision AS temp_base
  FROM base b
  JOIN agrae.lotes l ON l.idlote = b.idlote
  LEFT JOIN agro.cultivos c ON c.idcultivo = b.idcultivo
),
-- celda más cercana
nearest AS (
  SELECT
    lp.iddata,
    gp.id AS grid_id,
    round((lp.l_elev - gp.elev)::numeric, 2) AS dz_m
  FROM lote_pt lp
  JOIN LATERAL (
    SELECT id, elev, geom
    FROM weather.reticula
    ORDER BY geom <-> lp.pt
    LIMIT 1
  ) gp ON true
),
-- última fecha disponible por iddata/celda
last_fecha AS (
  SELECT
    n.iddata,
    least(current_date, max(g.fecha))::date AS last_fecha
  FROM nearest n
  JOIN weather.grid_era5_daily g ON g.grid_id = n.grid_id
  GROUP BY n.iddata
),
-- OBS: desde siembra hasta último dato
obs AS (
  SELECT
    lp.iddata,
    g.fecha::date AS fecha,
    g.tmean_c::double precision AS tmean,
    n.dz_m,
    lp.temp_base,
    lp.fechasiembra
  FROM lote_pt lp
  JOIN nearest n ON n.iddata = lp.iddata
  JOIN last_fecha lf ON lf.iddata = lp.iddata
  JOIN weather.grid_era5_daily g ON g.grid_id = n.grid_id
  WHERE lp.fechasiembra IS NOT NULL
    AND lp.temp_base IS NOT NULL
    AND g.fecha::date BETWEEN lp.fechasiembra AND lf.last_fecha
),
gdd AS (
  SELECT
    o.iddata,
    greatest(
      0.0,
      (o.tmean - (o.dz_m * (SELECT lapse_c_per_m FROM params))) - o.temp_base
    ) AS gdd_dia
  FROM obs o
),
gdd_acum AS (
  SELECT
    iddata,
    sum(gdd_dia) AS gdd_acum_obs
  FROM gdd
  GROUP BY iddata
),
objetivo AS (
  SELECT
    idcultivo,
    max(integral_acum_gd)::double precision AS gdd_objetivo
  FROM agro.cultivos_bbch_etapas
  GROUP BY idcultivo
),
-- etapa actual alcanzada (por gdd acumulado observado)
fenologia AS (
  SELECT
    b.iddata,
    b.idcultivo,
    ga.gdd_acum_obs,
    o.gdd_objetivo,
    lf.last_fecha AS fecha_ultimo_dato,
    ea.etapa AS etapa_actual,                 
    ea.bbch_desde AS bbch_actual,
    ea.bbch_hasta AS bbch_hasta_actual,
    ea.integral_acum_gd AS umbral_etapa_actual,
    CASE
      WHEN ga.gdd_acum_obs IS NULL OR o.gdd_objetivo IS NULL OR o.gdd_objetivo = 0 THEN NULL
      ELSE (ga.gdd_acum_obs / o.gdd_objetivo) * 100.0
    END AS avance_pct
  FROM base b
  LEFT JOIN gdd_acum ga ON ga.iddata = b.iddata
  LEFT JOIN objetivo o  ON o.idcultivo = b.idcultivo
  LEFT JOIN last_fecha lf ON lf.iddata = b.iddata
  LEFT JOIN LATERAL (
    SELECT e.*
    FROM agro.cultivos_bbch_etapas e
    WHERE e.idcultivo = b.idcultivo
      AND ga.gdd_acum_obs IS NOT NULL
      AND e.integral_acum_gd <= ga.gdd_acum_obs
    ORDER BY e.integral_acum_gd DESC
    LIMIT 1
  ) ea ON true
),
-- siguiente etapa (próximo umbral > actual)
siguiente AS (
  SELECT
    f.iddata,
    nx.bbch_desde AS bbch_siguiente,
    nx.bbch_hasta AS bbch_hasta_siguiente,
    nx.integral_acum_gd AS umbral_siguiente
  FROM fenologia f
  LEFT JOIN LATERAL (
    SELECT e.*
    FROM agro.cultivos_bbch_etapas e
    WHERE e.idcultivo = f.idcultivo
      AND f.gdd_acum_obs IS NOT NULL
      AND e.integral_acum_gd > COALESCE(f.umbral_etapa_actual, 0)
    ORDER BY e.integral_acum_gd ASC
    LIMIT 1
  ) nx ON true
),
/* =========================
   FUT: climatología por DOY (years_back) + acumulado futuro
   ========================= */
-- promedio por DOY para cada celda (últimos N años)
clima_doy AS (
  SELECT
    n.grid_id,
    extract(doy from x.fecha)::int AS doy,
    avg(x.tmean_c)::double precision AS tmean_clim
  FROM nearest n
  JOIN params p ON true
  JOIN weather.grid_era5_daily x ON x.grid_id = n.grid_id
  WHERE x.fecha >= (current_date - make_interval(years => p.years_back))
    AND x.fecha <  current_date
  GROUP BY n.grid_id, extract(doy from x.fecha)::int
),
-- días futuros por iddata
fut_days AS (
  SELECT
    b.iddata,
    n.grid_id,
    n.dz_m,
    lp.temp_base,
    f.fecha_ultimo_dato,
    (f.fecha_ultimo_dato + s.i)::date AS fecha,
    extract(doy from (f.fecha_ultimo_dato + s.i)::date)::int AS doy
  FROM base b
  JOIN lote_pt lp ON lp.iddata = b.iddata
  JOIN nearest n  ON n.iddata  = b.iddata
  JOIN fenologia f ON f.iddata = b.iddata
  CROSS JOIN LATERAL generate_series(1, (SELECT max_days_forward FROM params), 1) AS s(i)
  WHERE f.fecha_ultimo_dato IS NOT NULL
    AND lp.temp_base IS NOT NULL
),
fut AS (
  SELECT
    fd.iddata,
    fd.fecha,
    greatest(
      0.0,
      ((cd.tmean_clim - (fd.dz_m * (SELECT lapse_c_per_m FROM params))) - fd.temp_base)
    ) AS gdd_dia
  FROM fut_days fd
  JOIN clima_doy cd
    ON cd.grid_id = fd.grid_id
   AND cd.doy     = fd.doy
),
fut_acum AS (
  SELECT
    f.iddata,
    f.fecha,
    (SELECT ga.gdd_acum_obs FROM gdd_acum ga WHERE ga.iddata = f.iddata) +
    sum(f.gdd_dia) OVER (PARTITION BY f.iddata ORDER BY f.fecha) AS gdd_acum
  FROM fut f
),
-- fechas predichas: siguiente etapa y madurez (gdd_objetivo)
pred AS (
  SELECT
    f.iddata,
    min(f.fecha) FILTER (WHERE s.umbral_siguiente IS NOT NULL AND f.gdd_acum >= s.umbral_siguiente) AS fecha_bbch_siguiente_pred,
    min(f.fecha) FILTER (WHERE fo.gdd_objetivo     IS NOT NULL AND f.gdd_acum >= fo.gdd_objetivo)     AS fecha_madurez_pred
  FROM fut_acum f
  LEFT JOIN siguiente s ON s.iddata = f.iddata
  LEFT JOIN fenologia fo ON fo.iddata = f.iddata
  GROUP BY f.iddata
)
SELECT
  b.*,
  -- estado simple
  CASE
    WHEN b.idcultivo IS NULL THEN 'SIN CULTIVO'
    WHEN b.fechasiembra IS NULL THEN 'SIN FECHA SIEMBRA'
    WHEN f.gdd_acum_obs IS NULL THEN 'SIN CLIMA'
    WHEN f.bbch_actual IS NULL THEN 'PRE-BBCH'
    ELSE f.etapa_actual
  END AS estado_fenologia,
  -- f.fecha_ultimo_dato,
  -- BBCH actual (numérico) para simbología
  -- f.bbch_actual,
  -- f.bbch_hasta_actual,
  -- f.umbral_etapa_actual,
  -- siguiente BBCH (numérico) + fecha predicha
  -- s.bbch_siguiente,
  -- s.bbch_hasta_siguiente,
  -- s.umbral_siguiente,
  -- p.fecha_bbch_siguiente_pred,
  -- madurez (objetivo final)
  round(f.gdd_acum_obs::numeric,2) AS gdd_acum_obs,
  round(f.gdd_objetivo::numeric,2) AS gdd_objetivo,
  round(f.avance_pct::numeric,1)   AS avance_pct,
  p.fecha_madurez_pred as fechacosecha_pred
FROM base b
LEFT JOIN fenologia f ON f.iddata = b.iddata
LEFT JOIN siguiente s ON s.iddata = b.iddata
LEFT JOIN pred p      ON p.iddata = b.iddata