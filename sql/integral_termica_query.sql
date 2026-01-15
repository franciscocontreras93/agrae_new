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
    d.fertilizantecob1formula  AS formulacob1,
    d.fertilizantecob2formula  AS formulacob2,
    d.fertilizantecob3formula  AS formulacob3,
    d.fechasiembra::date AS fechasiembra,
    d.fechacosecha,
    d.prod_final,
    round((st_area(st_transform(l.geom,8857)) / 10000)::numeric,2) AS area_ha,
    l.elev AS l_elev,
    l.geom
  FROM agrae.lotes l
  JOIN campaign.data d ON d.idlote = l.idlote
  JOIN campaign.campanias c ON d.idcampania = c.id
  JOIN agrae.explotacion exp ON exp.idexplotacion = d.idexplotacion
  LEFT JOIN agrae.cultivo cult ON d.idcultivo = cult.idcultivo
  LEFT JOIN analytic.regimen reg ON reg.id  = d.idregimen
  WHERE d.idcampania = {} AND d.idexplotacion = {}
    -- AND d.fechasiembra IS NOT NULL
    -- AND d.idcultivo IS NOT NULL
),
params AS (
  SELECT
    10::int AS years_back,
    0.0065::double precision AS lapse_c_per_m,
    500::int AS max_days_forward
),
cultivo_param AS (
  SELECT
    b.*,
    st_centroid(b.geom) AS pt,
    c.temp_base::double precision AS temp_base
  FROM base b
  JOIN agro.cultivos c ON c.idcultivo = b.idcultivo
  WHERE c.temp_base IS NOT NULL
),
nearest AS (
  SELECT
    lp.iddata,
    gp.id AS grid_id,
    round((lp.l_elev - gp.elev)::numeric, 2) AS dz_m
  FROM cultivo_param lp
  JOIN LATERAL (
    SELECT id, elev, geom
    FROM weather.reticula
    ORDER BY geom <-> lp.pt
    LIMIT 1
  ) gp ON true
),
last_fecha AS (
  SELECT
    n.iddata,
    least(current_date, max(g.fecha))::date AS last_fecha
  FROM nearest n
  JOIN weather.grid_era5_daily g ON g.grid_id = n.grid_id
  GROUP BY n.iddata
),
obs_raw AS (
  SELECT
    lp.iddata,
    g.fecha::date AS fecha,
    g.tmean_c::double precision AS tmean,
    n.dz_m,
    lp.temp_base,
    lp.fechasiembra
  FROM cultivo_param lp
  JOIN nearest n    ON n.iddata = lp.iddata
  JOIN last_fecha lf ON lf.iddata = lp.iddata
  JOIN weather.grid_era5_daily g ON g.grid_id = n.grid_id
  WHERE g.fecha::date BETWEEN lp.fechasiembra AND lf.last_fecha
),
obs_gdd AS (
  SELECT
    o.iddata,
    o.fecha,
    greatest(
      0.0,
      (o.tmean - (o.dz_m * (SELECT lapse_c_per_m FROM params))) - o.temp_base
    ) AS gdd_dia
  FROM obs_raw o
),
estado AS (
  SELECT
    iddata,
    sum(gdd_dia) AS gdd_acum_obs,
    max(fecha)   AS fecha_ultimo_dato
  FROM obs_gdd
  GROUP BY iddata
),
objetivo AS (
  SELECT
    idcultivo,
    max(integral_acum_gd)::double precision AS gdd_objetivo
  FROM agro.cultivos_bbch_etapas
  GROUP BY idcultivo
),
etapa_actual AS (
  SELECT
    b.iddata,
    e.etapa,
    e.bbch_desde,
    e.bbch_hasta,
    e.integral_acum_gd AS umbral_etapa,
    CASE
      WHEN s.gdd_acum_obs IS NULL OR o.gdd_objetivo IS NULL OR o.gdd_objetivo = 0 THEN NULL
      ELSE (s.gdd_acum_obs / o.gdd_objetivo) * 100.0
    END AS avance_pct
  FROM cultivo_param b
  LEFT JOIN estado s   ON s.iddata = b.iddata
  LEFT JOIN objetivo o ON o.idcultivo = b.idcultivo
  LEFT JOIN LATERAL (
    SELECT *
    FROM agro.cultivos_bbch_etapas x
    WHERE x.idcultivo = b.idcultivo
      AND s.gdd_acum_obs IS NOT NULL
      AND x.integral_acum_gd <= s.gdd_acum_obs
    ORDER BY x.integral_acum_gd DESC
    LIMIT 1
  ) e ON true
),
clima_doy AS (
  SELECT
    n.iddata,
    extract(doy from x.fecha)::int AS doy,
    avg(x.tmean_c)::double precision AS tmean_clim
  FROM nearest n
  JOIN params p ON true
  JOIN weather.grid_era5_daily x ON x.grid_id = n.grid_id
  WHERE x.fecha >= (current_date - make_interval(years => p.years_back))
    AND x.fecha <  current_date
  GROUP BY n.iddata, extract(doy from x.fecha)::int
),
fut_days AS (
  SELECT
    b.iddata,
    (s.fecha_ultimo_dato + gs.i)::date AS fecha,
    extract(doy from (s.fecha_ultimo_dato + gs.i)::date)::int AS doy
  FROM cultivo_param b
  JOIN estado s ON s.iddata = b.iddata
  CROSS JOIN LATERAL generate_series(1, (SELECT max_days_forward FROM params), 1) AS gs(i)
),
fut_gdd AS (
  SELECT
    fd.iddata,
    fd.fecha,
    greatest(
      0.0,
      (cd.tmean_clim - (n.dz_m * (SELECT lapse_c_per_m FROM params))) - b.temp_base
    ) AS gdd_dia
  FROM fut_days fd
  JOIN cultivo_param b ON b.iddata = fd.iddata
  JOIN nearest n       ON n.iddata = fd.iddata
  JOIN clima_doy cd    ON cd.iddata = fd.iddata AND cd.doy = fd.doy
),
fut_acum AS (
  SELECT
    f.iddata,
    f.fecha,
    s.gdd_acum_obs + sum(f.gdd_dia) OVER (PARTITION BY f.iddata ORDER BY f.fecha) AS gdd_acum
  FROM fut_gdd f
  JOIN estado s ON s.iddata = f.iddata
),
pred AS (
  SELECT
    f.iddata,
    min(f.fecha) FILTER (WHERE o.gdd_objetivo IS NOT NULL AND f.gdd_acum >= o.gdd_objetivo) AS fechacosecha_pred
  FROM fut_acum f
  JOIN cultivo_param b ON b.iddata = f.iddata
  LEFT JOIN objetivo o ON o.idcultivo = b.idcultivo
  GROUP BY f.iddata
)
SELECT
 b.id,
  b.iddata,
  b.idcampania,
  b.idexplotacion,
  b.campania,
  b.explotacion,
  b.idlote,
  b.idcultivo,
  b.idregimen,
  b.lote,
  b.cultivo,
  b.prod_esperada,
  b.regimen,
  b.formulafondo,
  b.formulacob1,
  b.formulacob2,
  b.formulacob3,
  to_char(b.fechasiembra, 'YYYY-MM-DD') AS fechasiembra,
  to_char(b.fechacosecha, 'YYYY-MM-DD') AS fechacosecha,
  b.prod_final,
  b.area_ha::double precision AS area_ha,
  b.l_elev,
  to_char(s.fecha_ultimo_dato, 'YYYY-MM-DD') AS fecha_ultimo_dato,
  round(s.gdd_acum_obs::numeric,2)::double precision AS gdd_acum_obs,
  round(o.gdd_objetivo::numeric,2)::double precision AS gdd_objetivo,
  round(ea.avance_pct::numeric,1)::double precision AS avance_pct,
  COALESCE(ea.etapa, 'PRE-BBCH')   AS etapa_actual,
  to_char(p.fechacosecha_pred, 'YYYY-MM-DD') AS fechacosecha_pred,
  ST_AsText(st_multi(b.geom)) AS geom
FROM base b
LEFT JOIN estado s        ON s.iddata = b.iddata
LEFT JOIN objetivo o      ON o.idcultivo = b.idcultivo
LEFT JOIN etapa_actual ea ON ea.iddata = b.iddata
LEFT JOIN pred p          ON p.iddata = b.iddata
