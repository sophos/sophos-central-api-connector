/**********************************************************************\
| Parse the IOC JSON into useable objects                              |
\**********************************************************************/

WITH full_Key_Value AS
  (SELECT fullkey,
          value
   FROM json_tree(LOWER('$$IOC JSON$$'))
   WHERE TYPE NOT IN('array',
                     'object') ),
     fkv AS
  (SELECT SUBSTR(fullkey, INSTR(fullkey, "["), INSTR(fullkey, "]")-INSTR(fullkey, "[")+1) AS idx,
          CASE
              WHEN fullkey LIKE "%.indicator_type" THEN CAST(value AS TEXT)
          END AS indicator_type,
          CASE
              WHEN fullkey LIKE "%.data" THEN CAST(value AS TEXT)
          END AS ioc_data/*,
          CASE
              WHEN fullkey LIKE "%.note" THEN CAST(value AS TEXT)
          END AS ioc_description*/
   FROM full_Key_Value),
     ioc AS
  (SELECT a.idx AS aa,
          a.indicator_type AS indicator_type,
          b.ioc_data AS ioc_data/*,
          c.ioc_description AS ioc_description*/
   FROM fkv a
   INNER JOIN fkv b ON a.idx=b.idx
   /*INNER JOIN fkv c ON b.idx=c.idx*/
   WHERE a.indicator_type IS NOT NULL
     AND b.ioc_data IS NOT NULL
     /*AND c.ioc_description IS NOT NULL*/),

/**********************************************************************\
| The admin may want to search a large amount of data in the tables so |
| split time into 20 min chunks given the number hours specified       |
\**********************************************************************/

t_tbl(t_chunk) AS (
   VALUES ( (CAST ($$Start Search From$$ AS INT) ) )
   UNION ALL
   SELECT t_chunk+1200 FROM t_tbl WHERE t_chunk < (CAST ($$Start Search From$$ AS INT) + CAST( ($$Number of Hours of activity to search$$ * 3600) AS INT)))

/****************************************************************************\
| Check for matching domain or URL info seen in the specified lookback period|
\****************************************************************************/

SELECT
 CAST( datetime(spa.time,'unixepoch') AS TEXT) DATE_TIME,
 'MATCH FOUND' Detection,
 'sophos_process_activity' tbl_name,
 ioc.indicator_type,
 ioc.ioc_data,
 /*ioc.ioc_description,*/
 spa.subject,
 spa.SophosPID,
 CAST ( (select replace(spa.pathname, rtrim(spa.pathname, replace(spa.pathname, '\', '')), '')) AS TEXT) process_name,
 spa.action,
 spa.object,
 spa.url
FROM t_tbl
 LEFT JOIN ioc ON LOWER(ioc.indicator_type) IN ('domain', 'url')
 LEFT JOIN sophos_process_activity spa ON spa.subject IN ('Http','Url','Network') AND spa.time >= t_tbl.t_chunk and spa.time <= t_tbl.t_chunk+1200
WHERE spa.url LIKE ioc.ioc_data

UNION ALL

/****************************************************************************\
| Check for matching IP info seen in the specified lookback period           |
\****************************************************************************/

SELECT
 CAST( datetime(spa.time,'unixepoch') AS TEXT) DATE_TIME,
 'MATCH FOUND' Detection,
 'sophos_process_activity' tbl_name,
 ioc.indicator_type,
 ioc.ioc_data,
 /*ioc.ioc_description,*/
 spa.subject,
 spa.SophosPID,
 CAST ( (select replace(spa.pathname, rtrim(spa.pathname, replace(spa.pathname, '\', '')), '')) AS TEXT) process_name,
 spa.action,
 spa.object,
 spa.url
FROM t_tbl
 LEFT JOIN ioc ON LOWER(ioc.indicator_type) IN('ip')
 LEFT JOIN sophos_process_activity spa ON spa.subject IN ('Http','Ip','Network') AND spa.time >= t_tbl.t_chunk and spa.time <= t_tbl.t_chunk+1200
WHERE spa.source LIKE ioc.ioc_data OR spa.destination LIKE ioc.ioc_data

UNION ALL

/***********************************************************************************\
| Check for matching port info seen in the specified lookback period                |
\***********************************************************************************/

SELECT
 CAST( datetime(spa.time,'unixepoch') AS TEXT) DATE_TIME,
 'MATCH FOUND' Detection,
 'sophos_process_activity' tbl_name,
 ioc.indicator_type,
 ioc.ioc_data,
 /*ioc.ioc_description,*/
 spa.subject,
 spa.SophosPID,
 CAST ( (select replace(spa.pathname, rtrim(spa.pathname, replace(spa.pathname, '\', '')), '')) AS TEXT) process_name,
 spa.action,
 spa.object,
 spa.destinationPort
FROM t_tbl
 LEFT JOIN ioc ON LOWER(ioc.indicator_type) IN('port')
 LEFT JOIN sophos_process_activity spa ON spa.subject IN ('Http','Ip','Network') AND spa.time >= t_tbl.t_chunk and spa.time <= t_tbl.t_chunk+1200
WHERE spa.destinationPort LIKE ioc.ioc_data

UNION ALL

/***********************************************************************************\
| Check for matching sha256 info seen in the specified lookback period              |
\***********************************************************************************/

SELECT
 CAST( datetime(spj.time,'unixepoch') AS TEXT) DATE_TIME,
 'MATCH FOUND' Detection,
 'sophos_process_journal' tbl_name,
 ioc.indicator_type,
 ioc.ioc_data,
 /*ioc.ioc_description,*/
 'sophos_process_journal',
 spj.SophosPID,
 CAST ( (select replace(spj.pathname, rtrim(spj.pathname, replace(spj.pathname, '\', '')), '')) AS TEXT) process_name,
 spj.eventtype,
 'process execution',
 spj.sha256
FROM t_tbl
 LEFT JOIN ioc ON LOWER(ioc.indicator_type) IN('sha256')
 LEFT JOIN sophos_process_journal spj ON spj.time >= t_tbl.t_chunk and spj.time <= t_tbl.t_chunk+1200
WHERE LOWER(spj.sha256) LIKE LOWER(ioc.ioc_data)

UNION ALL

/***********************************************************************************\
| Check for matching process activity info seen in the specified lookback period|
\***********************************************************************************/

SELECT
 CAST( datetime(spa.time,'unixepoch') AS TEXT) DATE_TIME,
 'MATCH FOUND' Detection,
 'sophos_process_activity' tbl_name,
 ioc.indicator_type,
 ioc.ioc_data,
 /*ioc.ioc_description,*/
 spa.subject,
 spa.SophosPID,
 CAST ( (select replace(spa.pathname, rtrim(spa.pathname, replace(spa.pathname, '\', '')), '')) AS TEXT) process_name,
 spa.action,
 spa.object,
 spa.pathname
FROM t_tbl
 LEFT JOIN ioc ON LOWER(ioc.indicator_type) IN('pathname', 'file_path', 'file_path_name', 'filename')
 LEFT JOIN sophos_process_activity spa ON spa.subject IN ('Image','Process') AND spa.time >= t_tbl.t_chunk and spa.time <= t_tbl.t_chunk+1200
WHERE LOWER(spa.pathname) LIKE LOWER(ioc.ioc_data) OR LOWER(spa.object) LIKE LOWER(ioc.ioc_data)

UNION ALL

/***********************************************************************************\
| Check for matching file/directory on the CURRENT SATE of the device               |
\***********************************************************************************/

SELECT DISTINCT
 CAST( datetime(file.btime,'unixepoch') AS TEXT) DATE_TIME,
 'MATCH FOUND' Detection,
 'sophos_process_activity' tbl_name,
 ioc.indicator_type,
 ioc.ioc_data,
 /*ioc.ioc_description,*/
 'File_system',
 '' ,
 file.filename,
 'on disk',
 file.path,
 ''
FROM ioc
 LEFT JOIN file ON LOWER(ioc.indicator_type) IN('pathname', 'file_path', 'file_path_name', 'filename') AND file.path LIKE ioc.ioc_data
WHERE DATE_TIME <> ''