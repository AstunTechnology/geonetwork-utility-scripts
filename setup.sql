
-- View: metadata_xml

-- DROP VIEW metadata_xml;
CREATE OR REPLACE VIEW metadata_xml AS
SELECT metadata.id,
metadata.uuid,
metadata.schemaid,
metadata.istemplate,
metadata.isharvested,
metadata.createdate,
metadata.changedate,
XMLPARSE(DOCUMENT metadata.data STRIP WHITESPACE) AS data_xml,
metadata.data,
metadata.source,
metadata.title,
metadata.root,
metadata.harvestuuid,
metadata.owner,
metadata.doctype,
metadata.groupowner,
metadata.harvesturi,
metadata.rating,
metadata.popularity,
metadata.displayorder
FROM metadata;
ALTER TABLE metadata_xml
OWNER TO geonetwork;

-- View: records_update_cycle
 
-- DROP VIEW records_update_cycle;
 
CREATE OR REPLACE VIEW records_update_cycle AS
 SELECT metadata_xml.id,
    metadata_xml.changedate,
    array_to_string(xpath('/gmd:MD_Metadata/gmd:metadataMaintenance/gmd:MD_MaintenanceInformation/gmd:maintenanceAndUpdateFrequency/gmd:MD_MaintenanceFrequencyCode/text()'::text, metadata_xml.data_xml, '{{gco,http://www.isotc211.org/2005/gco},{gmd,http://www.isotc211.org/2005/gmd}}'::text[]), '-'::text) AS update_frequency,
    to_date(array_to_string(xpath('/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:date/gco:DateTime/text()'::text, metadata_xml.data_xml, '{{gco,http://www.isotc211.org/2005/gco},{gmd,http://www.isotc211.org/2005/gmd}}'::text[]), '-'::text), 'YYYY-MM-DD'::text) AS last_update_code,
    array_to_string(xpath('/gmd:MD_Metadata/gmd:metadataMaintenance/gmd:MD_MaintenanceInformation/gmd:userDefinedMaintenanceFrequency/gts:TM_PeriodDuration/text()'::text, metadata_xml.data_xml, '{{gco,http://www.isotc211.org/2005/gco},{gmd,http://www.isotc211.org/2005/gmd},{gts,http://www.isotc211.org/2005/gts}}'::text[]), '-'::text) AS last_update_user
   FROM metadata_xml
     LEFT JOIN groups ON metadata_xml.groupowner = groups.id;
 
ALTER TABLE records_update_cycle
  OWNER TO geonetwork;
COMMENT ON VIEW records_update_cycle
  IS 'View includes all records, showing:
- ID
- Date last changed
- Update frequency code
- Update frequency user-defined
';

-- Function: at_update_interval(text)
 
-- DROP FUNCTION at_update_interval(text);
 
CREATE OR REPLACE FUNCTION at_update_interval(update_frequency text)
  RETURNS interval AS
$BODY$
 
BEGIN
CASE WHEN update_frequency='monthly' THEN return '1 mons'::interval;
     WHEN update_frequency='quarterly' THEN return '3 mons'::interval;
     WHEN update_frequency='annually' THEN  return '1 yrs'::interval;
     WHEN update_frequency='daily' THEN  return '1 days'::interval;
     WHEN update_frequency='fortnightly' THEN return '2 weeks'::interval;
     WHEN update_frequency='weekly' THEN  return '1 weeks'::interval;
END CASE;
 END $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION at_update_interval(text)
  OWNER TO geonetwork;


