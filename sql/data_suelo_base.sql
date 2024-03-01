with data as (
    select distinct 
        c.indice_cosecha,
        c.contenidocosechac,
        c.contenidoresiduoc,
        round(d.prod_esperada / c.indice_cosecha) AS biomasa,
        round(d.prod_esperada / c.indice_cosecha - d.prod_esperada) AS residuo
    from campaign.data d 
    join agrae.cultivo c on c.idcultivo = d.idcultivo
    where d.idcampania = {} and d.idexplotacion = {} and d.idlote = {}
) select * from data