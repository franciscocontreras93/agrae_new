with values(iddata,idcultivo,idregimen,prod_esperada) as ({})
update campaign.data
	set idcultivo = q.idcultivo,
		idregimen = q.idregimen,
		prod_esperada = q.prod_esperada
from (select * from values) as q
where campaign.data.iddata = q.iddata;