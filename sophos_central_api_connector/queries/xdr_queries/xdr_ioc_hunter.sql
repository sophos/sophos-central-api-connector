WITH RECURSIVE
   -- Decompose the JSON structure into a temporary table
   Extract_from_JSON(idata, ind_type, ind_data, entry) AS (
      VALUES (lower('$$IOC_JSON$$'), json_extract_scalar('$$IOC_JSON$$', '$.ioc_data[0].indicator_type'), json_extract_scalar('$$IOC_JSON$$', '$.ioc_data[0].data'), 0)
      UNION ALL
      SELECT
         idata,
         json_extract_scalar(idata, '$.ioc_data['||CAST(entry+1 AS VARCHAR)||'].indicator_type'),
         json_extract_scalar(idata, '$.ioc_data['||CAST(entry+1 AS VARCHAR)||'].data'), entry + 1
      FROM Extract_from_JSON
      WHERE json_extract_scalar(idata, '$.ioc_data['||CAST(entry+1 AS VARCHAR)||'].indicator_type') > ''
   ),

   ioc_list (indicator_type, ioc_data) AS (
      SELECT
         LOWER(ind_type) ind_type,
         LOWER(REPLACE(ind_data,'\\','\')) ind_data  -- Convert path info with \\ to simply one \
      FROM
         Extract_from_JSON
      ORDER by entry ASC
   ),
Detections (timestamps, time, indicator_type, ioc_data, Detection_Type, ep_name, os_name, os_platform, os_version, name, path, sha1, sha256, destination_ip, domain, query_name) AS (
   SELECT
       timestamps AS time,
       time,
       ioc_list.indicator_type,
       ioc_list.ioc_data,
       CASE indicator_type
          WHEN 'ip' THEN (SELECT 'Destination IP MATCH' WHERE LOWER(destination_ip) LIKE ioc_data )
          WHEN 'domain' THEN (SELECT 'DOMAIN MATCH' WHERE LOWER(domain) LIKE ioc_data )
          WHEN 'url' THEN (SELECT 'DOMAIN MATCH' WHERE LOWER(domain) LIKE ioc_data )
          WHEN 'filepath' THEN (SELECT 'FilePath MATCH' WHERE LOWER(path) LIKE ioc_data )
          WHEN 'file_path' THEN (SELECT 'FilePath MATCH' WHERE LOWER(path) LIKE ioc_data )
          WHEN 'file_path_name' THEN (SELECT 'FilePath MATCH' WHERE LOWER(path) LIKE ioc_data )
          WHEN 'pathname' THEN (SELECT 'FilePath MATCH' WHERE LOWER(path) LIKE ioc_data )
          WHEN 'filename' THEN (SELECT 'FileName MATCH' WHERE LOWER(name) LIKE ioc_data )
          WHEN 'sha1' THEN (SELECT 'SHA1 MATCH' WHERE LOWER(sha1) LIKE ioc_data )
          WHEN 'sha256' THEN (SELECT 'SHA256 MATCH' WHERE LOWER(sha256) LIKE ioc_data )
          ELSE 'UNKNOWN MATCH METHOD'
       END Detection_Type,
       LOWER(meta_hostname) AS ep_name,
       meta_os_name AS os_name,
       meta_os_platform AS os_platform,
       meta_os_version AS os_version,
       name,
       path,
       sha1,
       sha256,
       destination_ip,
       domain,
       query_name
   FROM
      xdr_data
   JOIN ioc_list ON
      LOWER(domain) LIKE ioc_data OR
      LOWER(destination_ip) LIKE ioc_data  OR
      LOWER(path) LIKE ioc_data OR
      LOWER(sha1) LIKE ioc_data OR
      LOWER(sha256) LIKE ioc_data OR
	  LOWER(name) LIKE ioc_data
   )
SELECT
       *
FROM
     Detections
WHERE
      Detection_Type > ''