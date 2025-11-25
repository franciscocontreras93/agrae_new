WITH params AS (
    SELECT
        {}::int      AS idcampania,
        {}::int      AS idexplotacion,
        {}::int[]    AS idcultivo,      -- lista de idcultivo o NULL
        {}::int[]    AS iddata_list     -- lista de iddata o NULL
),
data AS (
    SELECT DISTINCT 
        d.iddata,
        d.idcampania,
        d.idexplotacion,
        ex.nombre AS explotacion,
        d.idlote,
        d.idcultivo,
        c.nombre AS cultivo,
        d.idregimen,
        d.fertilizantefondoformula,
        d.fertilizantefondoajustado,
        d.fertilizantecob1formula,
        d.fertilizantecob1ajustado,
        d.fertilizantecob2formula,
        d.fertilizantecob2ajustado,
        d.fertilizantecob3formula,
        d.fertilizantecob3ajustado,
        c.ms_cosecha,
        c.extraccioncosechan,
        c.extraccioncosechap,
        c.extraccioncosechak, 
        c.ms_residuo,
        c.extraccionresiduon,
        c.extraccionresiduop,
        c.extraccionresiduok, 
        c.cef_n,
        c.cef_p,
        c.cef_k,
        c.indice_cosecha,
        d.prod_esperada 
    FROM campaign.data d 
    LEFT JOIN agrae.cultivo c   ON c.idcultivo = d.idcultivo
    JOIN agrae.explotacion ex   ON d.idexplotacion = ex.idexplotacion
    JOIN params p               ON true
    WHERE
        (
            -- 🔹 Opción 1: lista de iddata => manda siempre
            p.iddata_list IS NOT NULL
            AND d.iddata = ANY (p.iddata_list)
        )
        OR (
            -- 🔹 Opción 2: sin lista de iddata => filtra por campaña/explotación
            p.iddata_list IS NULL
            AND d.idcampania   = p.idcampania
            AND d.idexplotacion = p.idexplotacion
            -- y si hay cultivos seleccionados, filtra por ellos
            AND (p.idcultivo IS NULL OR d.idcultivo = ANY (p.idcultivo))
        )
),
lotes as (select l.idlote, l.nombre, st_transform(st_buffer(st_transform(l.geom,8857),-0.5),4326) as geom, 
    d.iddata,
    d.idcampania,
    d.idexplotacion,
    d.idcultivo,
    d.idregimen as regimen,
    d.ms_cosecha,
    d.extraccioncosechan,
    d.extraccioncosechap,
    d.extraccioncosechak, 
    d.ms_residuo,
    d.extraccionresiduon,
    d.extraccionresiduop,
    d.extraccionresiduok, 
    d.prod_esperada from data d join agrae.lotes l on d.idlote = l.idlote ),
ambientes as (select distinct l.nombre as lote,a.idambiente,a.ambiente,a.ndvimax,st_asText(st_collectionextract(st_multi(st_intersection(l.geom,a.geometria)),3)) as geom, l.prod_esperada, l.idlote, l.iddata from agrae.ambiente a join lotes l on st_intersects(l.geom,a.geometria))
select row_number() over () as id , lote,ambiente,ndvimax::double precision,st_asText(geom) as geom from ambientes