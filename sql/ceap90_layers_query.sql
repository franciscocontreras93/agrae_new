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
), -- REQUIERE EL ID DE LA CAMPANIA Y DE LA EXPLOTACION
lotes as (select l.*, 
	d.iddata,
	d.idcampania,
	d.idexplotacion,
	d.idcultivo,
	d.idregimen as regimen
	from data d join agrae.lotes l on d.idlote = l.idlote ),
ceap as (select c.ce90 as ceap ,c.kf90 as kf,c.geometria as geom from agrae.ce c join lotes l on c.geometria && l.geom),
unidos as (select l.idlote,l.nombre as lote, c.ceap, c.kf, st_asText(c.geom) as geom from ceap c join lotes l on st_intersects(l.geom,c.geom))
select * from unidos