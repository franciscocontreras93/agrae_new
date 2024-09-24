with data as ( 	
	select distinct  	 	
	d.iddata, 	 	
	d.idcampania, 	 	
	d.idexplotacion, 	 	
	d.idlote, 	 	
	d.idcultivo, 	 	
	d.prod_esperada, 	 	
	d.prod_final,
	d.rinde_status,
	c.humedad, 	 	
	c.nombre as cultivo, 	 	
	c.indice_cosecha as ic 	 	
	from campaign.data d  	 	
	left join agrae.cultivo c on c.idcultivo = d.idcultivo 	 	
	where d.idcampania = {} and idexplotacion = {} and d.idcultivo is not null),
lotes as (select d.iddata,
l.idlote, 
d.idcultivo,
l.nombre,
d.cultivo, 
d.rinde_status as status,
d.prod_final
-- round((st_area(st_transform(l.geom,8857)) / 10000)::numeric,2) area_lote,
-- l.geom 
from data d join agrae.lotes l using(idlote))
select idcultivo,cultivo,round(sum(prod_final))::integer as prod_final from lotes
where status ='Pendiente' 
group by idcultivo,cultivo