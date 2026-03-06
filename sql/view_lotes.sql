select distinct 
d.iddata as id, 
d.iddata,
d.idcampania, 
d.idexplotacion,
c.nombre as campania,
exp.nombre as explotacion,
l.idlote, 
d.idcultivo,
d.idregimen,
l.nombre lote , 
cult.nombre cultivo,
d.prod_esperada::int,reg.nombre regimen,
--d.fertilizantefondoformula as formulafondo,
--d.fertilizantecob1formula as formulacob1,
--d.fertilizantecob2formula as formulacob2,
--d.fertilizantecob3formula as formulacob3,
d.fechasiembra , 
d.fechacosecha ,
d.prod_final,
round((st_area(st_transform(l.geom,8857)) / 10000)::numeric,2) as area_ha,
per.nombre || ' ' || per.apellidos as agricultor,
asesor.nombres as asesor,
-- round(ddc.dias_cobertura::numeric) ddc_mediana,
-- round(ddc.dias_cobertura::numeric *  round((st_area(st_transform(l.geom,8857)) / 10000)::numeric,2)) as ddc_mediana_x_area_ha,
l.geom from agrae.lotes l 
join campaign.data d on d.idlote = l.idlote
join campaign.campanias c on d.idcampania = c.id
join agrae.explotacion exp on exp.idexplotacion = d.idexplotacion
left join agrae.cultivo cult on d.idcultivo = cult.idcultivo
left join analytic.regimen reg on reg.id  = d.idregimen
left join agrae.agricultor ag using(idagricultor)
left join agrae.persona per on per.idpersona = ag.idpersona 
left join agrae.asesores asesor on ag.idasesor = asesor.idasesor 
-- LEFT JOIN (
--   SELECT 
--     da.idlote,
--     PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY da.dias_cobertura) AS dias_cobertura
--   FROM agrae.ddc_anual da
--   GROUP BY da.idlote
-- ) ddc ON ddc.idlote = d.idlote
WHERE d.idcampania = {} and d.idexplotacion = {}