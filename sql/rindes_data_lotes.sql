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
	where d.idcampania = {} and idexplotacion = {}),
lotes as (select d.iddata,l.idlote,l.nombre, d.cultivo, d.rinde_status as status, d.prod_final, l.geom from data d join agrae.lotes l using(idlote))
select distinct 
    l.iddata,
    l.nombre,
    l.cultivo,
    round(l.prod_final)::integer prod_final
from field.data_rindes dr 
join lotes l on dr.geom && l.geom 
where l.status ='Pendiente' 
group by l.iddata,l.nombre,l.cultivo,l.prod_final