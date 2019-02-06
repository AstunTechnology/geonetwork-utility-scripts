<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
    xmlns:gmd="http://www.isotc211.org/2005/gmd"
    xmlns:gco="http://www.isotc211.org/2005/gco"
    xmlns:atom="http://www.w3.org/2005/Atom"
    xmlns:inspire_dls="http://inspire.ec.europa.eu/schemas/inspire_dls/1.0"
    xmlns:georss="http://www.georss.org/georss"
    xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    
    
    <xsl:template match="@* | node()">
        <xsl:copy>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:copy>
    </xsl:template>
    
    <xsl:template match="/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date[position() !=1]"> 
        <xsl:message>Revision</xsl:message>
    </xsl:template>


    <!-- Find the update date section in the doc we're trying to update -->
    <xsl:template match="/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date[1]">
        <xsl:message>Creation</xsl:message>
        <!-- Ensure we copy the existing revision date node, our one is additional -->
        <xsl:copy-of select="."/>
        <!-- Get the dataset title, we need it later -->
        <xsl:variable name="datasetName">
            <xsl:value-of select="../gmd:title/gco:CharacterString"/>
        </xsl:variable>


        <!-- parse the latest remote liveproductfeed document -->
        <xsl:variable name="feed" select="document('https://www.ordnancesurvey.co.uk/xml/atom/LiveProductFeed.xml')/atom:feed"/>

        <!-- iterate through and find the entry with the identifier code that matches the dataset title -->
        <xsl:for-each select="$feed/atom:entry">

          <!-- fudge to strip line-breaks (yes, really) from liveproductfield identifier codes and find the one that matches our dataset title -->
            <xsl:if test="normalize-space(inspire_dls:spatial_dataset_identifier_code) =$datasetName">

              <!-- fudge to get date in same format as existing revision date, should work as single digits are given leading zeroes -->
              <xsl:variable name="updateDate" select="substring(atom:updated, 1, 10)" />

              <!-- add a new node with the new update date -->
                <gmd:date>
                    <gmd:CI_Date>
                        <gmd:date>
                    <gco:Date>
                        <xsl:value-of select="$updateDate"/>
                    </gco:Date>
                </gmd:date>
                <gmd:dateType>
                    <gmd:CI_DateTypeCode codeList="http://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/resources/codelist/ML_gmxCodelists.xml#CI_DateTypeCode"
                        codeListValue="revision"></gmd:CI_DateTypeCode>
                </gmd:dateType>
                    </gmd:CI_Date>
                </gmd:date>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>
    

</xsl:stylesheet>

