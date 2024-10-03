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
d.fertilizantefondoformula as formulafondo,
d.fertilizantecob1formula as formulacob1,
d.fertilizantecob2formula as formulacob2,
d.fertilizantecob3formula as formulacob3,
d.fechasiembra , 
d.fechacosecha ,
d.prod_final,
round((st_area(st_transform(l.geom,8857)) / 10000)::numeric,2) as area_ha,
l.geom from agrae.lotes l 
join campaign.data d on d.idlote = l.idlote
join campaign.campanias c on d.idcampania = c.id
join agrae.explotacion exp on exp.idexplotacion = d.idexplotacion
left join agrae.cultivo cult on d.idcultivo = cult.idcultivo
left join analytic.regimen reg on reg.id  = d.idregimen
WHERE d.idcampania = {} and d.idexplotacion = {}
