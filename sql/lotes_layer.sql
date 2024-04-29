WITH lotes AS (SELECT * FROM agrae.lotes), 
data as (select * from campaign.data) 
select distinct 
-- row_number() over () as id, 
l.idlote as id, 
l.nombre,(case when d.iddata is not null then 'Asignado' else 'No Asignado' end) as status, 
l.geom as geom
from lotes l left join data d on d.idlote = l.idlote