
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
 SELECT
    metadata_xml.id,
    metadata_xml.uuid,
    metadata_xml.changedate,
    btrim(xpath('/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceMaintenance/gmd:MD_MaintenanceInformation/gmd:maintenanceAndUpdateFrequency/gmd:MD_MaintenanceFrequencyCode/@codeListValue'::text, metadata_xml.data_xml, '{{gco,http://www.isotc211.org/2005/gco},{gmd,http://www.isotc211.org/2005/gmd}}'::text[])::text, '{}') AS update_frequency,
    to_date(array_to_string(xpath('/gmd:MD_Metadata/gmd:dateStamp/gco:DateTime/text()'::text, metadata_xml.data_xml, '{{gco,http://www.isotc211.org/2005/gco},{gmd,http://www.isotc211.org/2005/gmd}}'::text[]), '-'::text), 'YYYY-MM-DD'::text) AS last_update_code,
    array_to_string(xpath('/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceMaintenance/gmd:MD_MaintenanceInformation/gmd:userDefinedMaintenanceFrequency/gts:TM_PeriodDuration/text()'::text, metadata_xml.data_xml, '{{gco,http://www.isotc211.org/2005/gco},{gmd,http://www.isotc211.org/2005/gmd},{gts,http://www.isotc211.org/2005/gts}}'::text[]), '-'::text) AS last_update_user,
    array_to_string(xpath('/gmd:MD_Metadata/gmd:contact/gmd:CI_ResponsibleParty/gmd:individualName/gco:CharacterString/text()'::text, metadata_xml.data_xml, '{{gco,http://www.isotc211.org/2005/gco},{gmd,http://www.isotc211.org/2005/gmd},{gts,http://www.isotc211.org/2005/gts}}'::text[]), '-'::text) AS contact,
    array_to_string(xpath('/gmd:MD_Metadata/gmd:contact/gmd:CI_ResponsibleParty/gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:electronicMailAddress/gco:CharacterString/text()'::text, metadata_xml.data_xml, '{{gco,http://www.isotc211.org/2005/gco},{gmd,http://www.isotc211.org/2005/gmd},{gts,http://www.isotc211.org/2005/gts}}'::text[]), '-'::text) AS email_contact,
    array_to_string(xpath('/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString/text()'::text, metadata_xml.data_xml, '{{gco,http://www.isotc211.org/2005/gco},{gmd,http://www.isotc211.org/2005/gmd},{gts,http://www.isotc211.org/2005/gts}}'::text[]), '-'::text) AS title,
    array_to_string(xpath('/gmd:MD_Metadata/gmd:hierarchyLevel/gmd:MD_ScopeCode/@codeListValue/.'::text, metadata_xml.data_xml, '{{gco,http://www.isotc211.org/2005/gco},{gmd,http://www.isotc211.org/2005/gmd},{gts,http://www.isotc211.org/2005/gts}}'::text[]), '-'::text) AS type,
    concat('http://geonetwork.astuntechnology.com/geonetwork/astuntest/eng/catalog.search#/metadata/', array_to_string(xpath('/gmd:MD_Metadata/gmd:fileIdentifier/gco:CharacterString/text()'::text, metadata_xml.data_xml, '{{gco,http://www.isotc211.org/2005/gco},{gmd,http://www.isotc211.org/2005/gmd},{gts,http://www.isotc211.org/2005/gts}}'::text[]), '-'::text)) AS link
   FROM metadata_xml
     LEFT JOIN groups ON metadata_xml.groupowner = groups.id
  WHERE metadata_xml.istemplate = 'n'::bpchar;

ALTER TABLE records_update_cycle
  OWNER TO geonetwork;
COMMENT ON VIEW records_update_cycle
  IS
'View includes all records, showing:
- UUID
- ID
- Date last changed
- Update frequency code
- Update frequency user-defined
- Update contact name
- Update contact email
- Title of metadata record
- Type of record (dataset or service)
- Link to record in catalogue
';


-- Function: at_update_interval(text)

-- DROP FUNCTION at_update_interval(text);

CREATE OR REPLACE FUNCTION at_update_interval(update_frequency text)
  RETURNS interval AS
$BODY$

BEGIN
CASE WHEN update_frequency='monthly' THEN return '1 mons'::interval;
     WHEN update_frequency='quarterly' THEN return '3 mons'::interval;
     WHEN update_frequency='annually' THEN return '1 yrs'::interval;
     WHEN update_frequency='daily' THEN return '1 days'::interval;
     WHEN update_frequency='fortnightly' THEN return '2 weeks'::interval;
     WHEN update_frequency='weekly' THEN return '1 weeks'::interval;
     WHEN update_frequency='biannually' THEN return '2 yrs'::interval;
     WHEN update_frequency='unknown' THEN return '3 mons'::interval;
     WHEN update_frequency='asNeeded' THEN return '1 mons'::interval;
END CASE;
 END $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION at_update_interval(text)
  OWNER TO geonetwork;


-- Function: at_update_reminder(text)

-- DROP FUNCTION at_update_reminder(text);

CREATE OR REPLACE FUNCTION at_update_reminder(update_frequency text)
  RETURNS interval AS
$BODY$

BEGIN
CASE WHEN update_frequency='monthly' THEN return '1 weeks'::interval;
     WHEN update_frequency='quarterly' THEN return '1 weeks'::interval;
     WHEN update_frequency='annually' THEN  return '1 mons'::interval;
     WHEN update_frequency='daily' THEN  return '1 days'::interval;
     WHEN update_frequency='fortnightly' THEN return '2 days'::interval;
     WHEN update_frequency='weekly' THEN  return '2 days'::interval;
     WHEN update_frequency='biannually' THEN return '1 yrs'::interval;
     WHEN update_frequency='unknown' THEN return '1 weeks'::interval;
     WHEN update_frequency='asNeeded' THEN return '2 days'::interval;
END CASE;
 END $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION at_update_reminder(text)
  OWNER TO geonetwork;
