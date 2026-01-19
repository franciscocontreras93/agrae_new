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
  AND d.fechasiembra IS NOT NULL
  AND d.idcultivo IS NOT NULL
),params AS (
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

/* =========================
   OBS (1 punto) + GDD diario + acumulado
   ========================= */
obs_raw AS (
  SELECT
    lp.iddata,
    g.fecha::date AS fecha,
    g.tmean_c::double precision AS tmean,
    n.dz_m,
    lp.temp_base,
    lp.fechasiembra
  FROM cultivo_param lp
  JOIN nearest n     ON n.iddata = lp.iddata
  JOIN last_fecha lf ON lf.iddata = lp.iddata
  JOIN weather.grid_era5_daily g ON g.grid_id = n.grid_id
  WHERE lp.fechasiembra IS NOT NULL
    AND g.fecha::date BETWEEN lp.fechasiembra AND lf.last_fecha
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

obs_acum AS (
  SELECT
    g.*,
    sum(g.gdd_dia) OVER (PARTITION BY g.iddata ORDER BY g.fecha) AS gdd_acum
  FROM obs_gdd g
),

estado AS (
  SELECT
    iddata,
    max(gdd_acum) AS gdd_acum_obs,
    max(fecha)    AS fecha_ultimo_dato
  FROM obs_acum
  GROUP BY iddata
),

/* =========================
   Objetivo final por cultivo
   ========================= */
objetivo AS (
  SELECT
    idcultivo,
    max(integral_acum_gd)::double precision AS gdd_objetivo
  FROM agro.cultivos_bbch_etapas
  GROUP BY idcultivo
),

/* =========================
   Etapa actual (sin bbch_hasta)
   ========================= */
etapa_actual AS (
  SELECT
    b.iddata,
    e.etapa,
    e.bbch_desde,
    e.integral_acum_gd AS umbral_etapa,
    CASE
      WHEN s.gdd_acum_obs IS NULL OR o.gdd_objetivo IS NULL OR o.gdd_objetivo = 0 THEN NULL
      ELSE (s.gdd_acum_obs / o.gdd_objetivo) * 100.0
    END AS avance_pct
  FROM cultivo_param b
  LEFT JOIN estado s   ON s.iddata = b.iddata
  LEFT JOIN objetivo o ON o.idcultivo = b.idcultivo
  LEFT JOIN LATERAL (
    SELECT
      x.etapa, x.bbch_desde, x.integral_acum_gd
    FROM agro.cultivos_bbch_etapas x
    WHERE x.idcultivo = b.idcultivo
      AND s.gdd_acum_obs IS NOT NULL
      AND x.integral_acum_gd <= s.gdd_acum_obs
    ORDER BY x.integral_acum_gd DESC
    LIMIT 1
  ) e ON true
),

/* =========================
   FUT: climatología por DOY (10 años) + acumulado futuro
   ========================= */
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
    s.gdd_acum_obs
    + sum(f.gdd_dia) OVER (PARTITION BY f.iddata ORDER BY f.fecha) AS gdd_acum
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
),

/* =========================
   MANEJOS POR UMBRAL (rangos)
   ========================= */
manejo_umbral AS (
  SELECT
    e.idcultivo,
    e.id_manejo,
    min(e.integral_acum_gd)::double precision AS gdd_umbral
  FROM agro.cultivos_bbch_etapas e
  WHERE e.id_manejo IS NOT NULL
  GROUP BY e.idcultivo, e.id_manejo
),

manejo_orden AS (
  SELECT
    mu.*,
    lag(mu.id_manejo)  OVER (PARTITION BY mu.idcultivo ORDER BY mu.gdd_umbral) AS id_manejo_prev,
    lag(mu.gdd_umbral) OVER (PARTITION BY mu.idcultivo ORDER BY mu.gdd_umbral) AS gdd_umbral_prev,
    lead(mu.id_manejo)  OVER (PARTITION BY mu.idcultivo ORDER BY mu.gdd_umbral) AS id_manejo_next,
    lead(mu.gdd_umbral) OVER (PARTITION BY mu.idcultivo ORDER BY mu.gdd_umbral) AS gdd_umbral_next
  FROM manejo_umbral mu
),

/* último umbral alcanzado */
manejo_reached AS (
  SELECT
    b.iddata,
    mr.id_manejo,
    mr.gdd_umbral,
    mr.id_manejo_prev,
    mr.gdd_umbral_prev,
    mr.id_manejo_next,
    mr.gdd_umbral_next
  FROM cultivo_param b
  LEFT JOIN estado s ON s.iddata = b.iddata
  LEFT JOIN LATERAL (
    SELECT mo.*
    FROM manejo_orden mo
    WHERE mo.idcultivo = b.idcultivo
      AND s.gdd_acum_obs IS NOT NULL
      AND s.gdd_acum_obs >= mo.gdd_umbral
    ORDER BY mo.gdd_umbral DESC
    LIMIT 1
  ) mr ON true
),

/* primer umbral futuro (next real) */
manejo_next_row AS (
  SELECT
    b.iddata,
    nx.id_manejo,
    nx.gdd_umbral
  FROM cultivo_param b
  LEFT JOIN estado s ON s.iddata = b.iddata
  LEFT JOIN LATERAL (
    SELECT mu.*
    FROM manejo_umbral mu
    WHERE mu.idcultivo = b.idcultivo
      AND s.gdd_acum_obs IS NOT NULL
      AND s.gdd_acum_obs < mu.gdd_umbral
    ORDER BY mu.gdd_umbral ASC
    LIMIT 1
  ) nx ON true
),

/* resolver prev/current/next con regla SM */
manejo_calc AS (
  SELECT
    b.iddata,

    /* CURRENT: entre umbral alcanzado y el siguiente => es el alcanzado
       si alcanzó el último => SM
       si no alcanzó ninguno => SM
    */
    CASE
      WHEN s.gdd_acum_obs IS NULL THEN NULL
      WHEN mr.id_manejo IS NULL THEN 'SM'
      WHEN mr.gdd_umbral_next IS NULL THEN 'SM'
      ELSE mcur.codigo
    END AS manejo_cur_codigo,
    CASE
      WHEN s.gdd_acum_obs IS NULL THEN NULL
      WHEN mr.id_manejo IS NULL THEN 'Sin Manejo'
      WHEN mr.gdd_umbral_next IS NULL THEN 'Sin Manejo'
      ELSE mcur.nombre
    END AS manejo_cur_nombre,
    CASE
      WHEN mr.id_manejo IS NULL THEN NULL
      ELSE mr.gdd_umbral
    END AS manejo_cur_umbral,

    /* PREV:
       - antes del primer umbral => SM
       - entre umbrales => el anterior del current (si no existe => SM)
       - después del último => el último manejo (mr)
    */
    CASE
      WHEN s.gdd_acum_obs IS NULL THEN NULL
      WHEN mr.id_manejo IS NULL THEN 'SM'
      WHEN mr.gdd_umbral_next IS NULL THEN mlast.codigo
      WHEN mr.id_manejo_prev IS NULL THEN 'SM'
      ELSE mprev.codigo
    END AS manejo_prev_codigo,
    CASE
      WHEN s.gdd_acum_obs IS NULL THEN NULL
      WHEN mr.id_manejo IS NULL THEN 'Sin Manejo'
      WHEN mr.gdd_umbral_next IS NULL THEN mlast.nombre
      WHEN mr.id_manejo_prev IS NULL THEN 'Sin Manejo'
      ELSE mprev.nombre
    END AS manejo_prev_nombre,
    CASE
      WHEN mr.id_manejo IS NULL THEN NULL
      WHEN mr.gdd_umbral_next IS NULL THEN mr.gdd_umbral
      ELSE mr.gdd_umbral_prev
    END AS manejo_prev_umbral,

    /* NEXT:
       - antes del primer => primero real
       - entre umbrales => el siguiente real
       - después del último => SM
    */
    CASE
      WHEN s.gdd_acum_obs IS NULL THEN NULL
      WHEN mr.id_manejo IS NOT NULL AND mr.gdd_umbral_next IS NULL THEN 'SM'
      WHEN nx.id_manejo IS NULL THEN 'SM'
      ELSE mnext.codigo
    END AS manejo_next_codigo,
    CASE
      WHEN s.gdd_acum_obs IS NULL THEN NULL
      WHEN mr.id_manejo IS NOT NULL AND mr.gdd_umbral_next IS NULL THEN 'Sin Manejo'
      WHEN nx.id_manejo IS NULL THEN 'Sin Manejo'
      ELSE mnext.nombre
    END AS manejo_next_nombre,
    CASE
      WHEN nx.id_manejo IS NULL THEN NULL
      ELSE nx.gdd_umbral
    END AS manejo_next_umbral

  FROM cultivo_param b
  LEFT JOIN estado s ON s.iddata = b.iddata
  LEFT JOIN manejo_reached mr ON mr.iddata = b.iddata
  LEFT JOIN manejo_next_row nx ON nx.iddata = b.iddata

  LEFT JOIN agro.manejo mcur  ON mcur.id_manejo  = mr.id_manejo
  LEFT JOIN agro.manejo mprev ON mprev.id_manejo = mr.id_manejo_prev
  LEFT JOIN agro.manejo mlast ON mlast.id_manejo = mr.id_manejo
  LEFT JOIN agro.manejo mnext ON mnext.id_manejo = nx.id_manejo
),

/* fechas esperadas/alcanzadas para prev/current/next */
manejo_fechas AS (
  SELECT
    b.iddata,

    /* PREV: fecha cuando se alcanzó el umbral prev (si es SM => NULL) */
    CASE
      WHEN mc.manejo_prev_codigo IS NULL OR mc.manejo_prev_codigo = 'SM' THEN NULL
      ELSE (
        SELECT min(o.fecha)
        FROM obs_acum o
        WHERE o.iddata = b.iddata
          AND o.gdd_acum >= mc.manejo_prev_umbral
      )
    END AS fecha_manejo_prev,

    /* CURRENT: fecha cuando se alcanzó el umbral current (si current=SM => NULL) */
    CASE
      WHEN mc.manejo_cur_codigo IS NULL OR mc.manejo_cur_codigo = 'SM' THEN NULL
      ELSE (
        SELECT min(o.fecha)
        FROM obs_acum o
        WHERE o.iddata = b.iddata
          AND o.gdd_acum >= mc.manejo_cur_umbral
      )
    END AS fecha_manejo_cur,

    /* NEXT: fecha predicha cuando se alcanzará el umbral next (si SM => NULL) */
    CASE
      WHEN mc.manejo_next_codigo IS NULL OR mc.manejo_next_codigo = 'SM' THEN NULL
      ELSE (
        SELECT min(f.fecha)
        FROM fut_acum f
        WHERE f.iddata = b.iddata
          AND f.gdd_acum >= mc.manejo_next_umbral
      )
    END AS fecha_manejo_next

  FROM cultivo_param b
  LEFT JOIN manejo_calc mc ON mc.iddata = b.iddata
)
SELECT
  b.id,
  -- b.iddata,
  -- b.idcampania,
  -- b.idexplotacion,
  b.campania,
  b.explotacion,
  -- b.idlote,
  -- b.idcultivo,
  -- b.idregimen,
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
  -- b.prod_final,
  b.area_ha::double precision AS area_ha,
  round(b.l_elev) l_elev,
  -- to_char(s.fecha_ultimo_dato, 'YYYY-MM-DD') AS fecha_ultimo_dato,
  round(s.gdd_acum_obs::numeric,2)::double precision AS it_acumulada,
  round(o.gdd_objetivo::numeric,2)::double precision AS it_objetivo,
  round(ea.avance_pct::numeric,1)::double precision AS avance_pct,
  COALESCE(ea.etapa, 'N/D') AS etapa_actual,
  /* manejo prev/current/next + fechas */
  mc.manejo_prev_codigo,
  mc.manejo_prev_nombre,
  to_char(mf.fecha_manejo_prev, 'YYYY-MM-DD') AS fecha_manejo_prev,
  mc.manejo_cur_codigo,
  mc.manejo_cur_nombre,
  to_char(mf.fecha_manejo_cur, 'YYYY-MM-DD') AS fecha_manejo_cur,
  mc.manejo_next_codigo,
  mc.manejo_next_nombre,
  to_char(mf.fecha_manejo_next, 'YYYY-MM-DD') AS fecha_manejo_next,
  to_char(p.fechacosecha_pred, 'YYYY-MM-DD') AS fechacosecha_pred,
  ST_AsText(st_multi(b.geom)) AS geom
FROM base b
LEFT JOIN estado s        ON s.iddata = b.iddata
LEFT JOIN objetivo o      ON o.idcultivo = b.idcultivo
LEFT JOIN etapa_actual ea ON ea.iddata = b.iddata
LEFT JOIN pred p          ON p.iddata = b.iddata
LEFT JOIN manejo_calc mc  ON mc.iddata = b.iddata
LEFT JOIN manejo_fechas mf ON mf.iddata = b.iddata;