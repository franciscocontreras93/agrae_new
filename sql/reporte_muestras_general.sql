-- QUERY PARA GENERAR EL REPORTE DE MUESTRAS ANALIZADAS Y PENDIENTE POR ANALIZAR, TAMBIEN IMPLEMENTA
-- LO MUESTREADO EN CAMPO Y LO PENDIENTE POR MUESTREAR 

select m.codigo, c.nombre campania,ex.idexplotacion ,ex.nombre explotacion,upper(l.nombre) lote,m.segmento,s.status,a.*  from field.muestras m
join campaign.campanias c on c.id = m.idcampania 
join agrae.explotacion ex on ex.idexplotacion = m.idexplotacion
join (select idlote,nombre from agrae.lotes) as l on l.idlote = m.idlote
join correlations.status s on m.status  = s.id 
left join analytic.analitica a on m.codigo = a.cod
where c.id = {}


