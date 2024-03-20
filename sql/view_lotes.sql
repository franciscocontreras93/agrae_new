select row_number() over () as id, 
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
d.fechasiembra , 
d.fechacosecha , 
(st_area(st_transform(l.geom,8857)) / 10000) area_ha,
st_asText(l.geom) geom from agrae.lotes l 
join campaign.data d on d.idlote = l.idlote
join campaign.campanias c on d.idcampania = c.id
join agrae.explotacion exp on exp.idexplotacion = d.idexplotacion
left join agrae.cultivo cult on d.idcultivo = cult.idcultivo
left join analytic.regimen reg on reg.id  = d.idregimen
WHERE d.idcampania = {} 
