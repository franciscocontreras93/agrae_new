update campaign.data 
    set prod_final = datos.produccion,
        rinde_status = 'Ajustado'
from (
    values
        {}
) as datos(produccion,id)
where iddata = datos.id::integer