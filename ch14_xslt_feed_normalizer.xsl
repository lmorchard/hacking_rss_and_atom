<?xml version='1.0' encoding='utf-8'?>
<!--
    ch14_xslt_feed_normalizer.xsl

    Normalize feed data from Atom and RSS feeds and output 
    a new feed in either format, based on 'format' parameter.
-->
<xsl:stylesheet 
    version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
    xmlns:atom="http://purl.org/atom/ns#"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:rss10="http://purl.org/rss/1.0/"
    xmlns:rss09="http://my.netscape.com/rdf/simple/0.9/"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:dcterms="http://purl.org/dc/terms/"
    xmlns:content="http://purl.org/rss/1.0/modules/content/"
    xmlns:l="http://purl.org/rss/1.0/modules/link/"
    xmlns:xhtml="http://www.w3.org/1999/xhtml"
    xmlns:date="http://exslt.org/dates-and-times"
    extension-element-prefixes="date">

    <xsl:import href="http://www.exslt.org/date/functions/format-date/date.format-date.function.xsl" />

    <xsl:output method="xml" indent="yes" encoding="utf-8" />

    <!-- format parameter expected as 'atom' or 'rss' -->
    <xsl:param name="format" select="'atom'" />

    <!-- Main driver template, switches between output formats -->
    <xsl:template match="/">
        <xsl:choose> 
            <xsl:when test="$format='rss'">
                <xsl:call-template name="rss20.feed" />
            </xsl:when>
            <xsl:when test="$format='timetest'">
                <xsl:call-template name="rfc822_to_w3cdtf">
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="atom03.feed" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- Atom 0.3 feed output shell template -->
    <xsl:template name="atom03.feed">
        <feed xmlns="http://purl.org/atom/ns#" version="0.3">
            <title><xsl:value-of select="$feed.title"/></title>
            <tagline><xsl:value-of select="$feed.description"/></tagline>
            <link rel="alternate" type="text/html" href="{$feed.link}" />
            <modified><xsl:value-of select="$feed.date" /></modified>
            <xsl:if test="$feed.author.name and $feed.author.email">
                <author>
                    <name><xsl:value-of select="$feed.author.name" /></name>
                    <email><xsl:value-of select="$feed.author.email" /></email>
                </author>
            </xsl:if>
            <xsl:call-template name="process_entries" />
        </feed>
    </xsl:template>
    
    <!-- Atom 0.3 entry output template -->
    <xsl:template name="atom03.entry">
        <entry xmlns="http://purl.org/atom/ns#">
            <title><xsl:value-of select="$entry.title" /></title>
            <link rel="alternate" type="text/html" href="{$entry.link}" />
            <id><xsl:value-of select="$entry.id" /></id>
            <xsl:if test="$entry.author.name and $entry.author.email">
                <author>
                    <name><xsl:value-of select="$entry.author.name" /></name>
                    <email><xsl:value-of select="$entry.author.email" /></email>
                </author>
            </xsl:if>
            <issued><xsl:value-of select="$entry.date" /></issued>
            <modified><xsl:value-of select="$entry.date" /></modified>
            <summary><xsl:value-of select="$entry.summary" /></summary>
        </entry>
    </xsl:template>

    <!-- RSS 2.0 feed output shell template -->
    <xsl:template name="rss20.feed">
        <rss version="2.0">        
            <channel> 
                <title><xsl:value-of select="$feed.title"/></title>  
                <description>
                    <xsl:value-of select="$feed.description"/>
                </description>
                <link><xsl:value-of select="$feed.link"/></link>   
                <pubDate>
                    <xsl:call-template name="w3cdtf_to_rfc822">
                        <xsl:with-param name="date" select="$feed.date" />
                    </xsl:call-template>
                </pubDate>        
                <xsl:if test="$feed.author.email">
                    <managingEditor>
                        <xsl:value-of select="$feed.author.email" />
                    </managingEditor>
                </xsl:if>
                <xsl:call-template name="process_entries" />
            </channel>
        </rss>
    </xsl:template>

    <!-- RSS 2.0 entry output template -->
    <xsl:template name="rss20.entry">
        <item>
            <title><xsl:value-of select="$entry.title"/></title>  
            <link><xsl:value-of select="$entry.link"/></link>   
            <pubDate>
                <xsl:call-template name="w3cdtf_to_rfc822">
                    <xsl:with-param name="date" select="$entry.date" />
                </xsl:call-template>
            </pubDate>        
            <guid><xsl:value-of select="$entry.id" /></guid>
            <description>
                <xsl:value-of select="$entry.summary"/>
            </description>
        </item>
    </xsl:template>

    <!-- Extract feed title content -->
    <xsl:variable name="feed.title"   
        select="/atom:feed/atom:title |
                /rdf:RDF/rss10:channel/rss10:title |
                /rdf:RDF/rss10:channel/dc:title |
                /rdf:RDF/rss09:channel/rss09:title |
                /rss/channel/title |
                /rss/channel/dc:title" />

    <!-- Extract feed.description / description -->
    <xsl:variable name="feed.description"
        select="/atom:feed/atom:tagline |
                /rss/channel/description |
                /rss/channel/dc:description |
                /rdf:RDF/rss10:channel/rss10:description |
                /rdf:RDF/rdf:channel/rdf:description |
                /rdf:RDF/rdf:channel/dc:description" />

    <!-- Extract feed authorship info -->
    <xsl:variable name="feed.author.email"
        select="/atom:feed/atom:author/atom:email |
                /rss/channel/managingEditor |
                /rss/channel/dc:creator |
                /rss/channel/dc:author |
                /rdf:RDF/rss10:channel/dc:creator |
                /rdf:RDF/rss10:channel/dc:author |
                /rdf:RDF/rdf:channel/dc:creator |
                /rdf:RDF/rdf:channel/dc:author" />
            
    <!-- Extract feed authorship info -->
    <xsl:variable name="feed.author.name"
        select="/atom:feed/atom:author/atom:name | $feed.author.email" />

    <!-- Extract various interpretations of feed link -->
    <xsl:variable name="feed.link"   
        select="/atom:feed/atom:link[@rel='alternate' and 
                    ( @type='text/html' or 
                      @type='application/xhtml+xml' )]/@href |
                    
                /rss/channel/link |
                /rss/channel/dc:relation/@rdf:resource |
                /rss/channel/item/l:link[@l:rel='permalink' and 
                    ( @l:type='text/html' or
                      @l:type='application/xhtml+xml' )]/@rdf:resource |
                    
                /rdf:RDF/rss09:channel/rss09:link |
                /rdf:RDF/rss10:channel/rss10:link |
                /rdf:RDF/rss10:channel/dc:relation/@rdf:resource |
                /rdf:RDF/rss10:item/l:link[@l:rel='permalink' and 
                    ( @l:type='text/html' or
                      @l:type='application/xhtml+xml' )]/@rdf:resource" />

    <!-- Extract feed publish date -->
    <xsl:variable name="feed.date">
        <xsl:choose>
            <!-- If RSS 2.0 pubDate found, perform RFC822 conversion -->
            <xsl:when test="/rss/channel/pubDate">
                <xsl:call-template name="rfc822_to_w3cdtf">
                    <xsl:with-param name="date" 
                        select="/rss/channel/pubDate" />
                </xsl:call-template>
            </xsl:when>
            <!-- All other date formats are assumed W3CDTF / ISO8601 -->
            <xsl:otherwise>
                <xsl:value-of
                    select="/atom:feed/atom:modified |
                            /rss/channel/dc:date |
                            /rdf:RDF/rss10:channel/dc:date |
                            /rdf:RDF/rdf:channel/dc:date |
                            /rdf:RDF/rdf:channel/dcterms:modified" />
            </xsl:otherwise> 
        </xsl:choose>
    </xsl:variable>

    <xsl:template name="process_entries">

        <!-- Find and process all feed entries -->
        <xsl:for-each 
            select="/atom:feed/atom:entry | 
                    /rdf:RDF/rss10:item | 
                    /rdf:RDF/rss09:item | 
                    /rss/channel/item">

            <!-- Extract entry title -->
            <xsl:variable name="entry.title"
                select="atom:title | title | dc:title | 
                        rdf:title | rss10:title" />

                    
            <!-- Extract entry GUID -->
            <xsl:variable name="entry.id"
                select="atom:id | @rdf:about |
                        guid[not(@isPermaLink) or @isPermaLink='true']| 
                        link"/>

            <!-- Extract entry authorship -->
            <xsl:variable name="entry.author.email"
                select="atom:author/atom:email | dc:creator | dc:author" />
            <xsl:variable name="entry.author.name"
                select="atom:author/atom:name | $entry.author.email" />

            <!-- Extract entry summary content -->
            <xsl:variable name="entry.summary"
                select="atom:summary | description | dc:description | 
                        rdf:description | rss10:description" />

            <!-- Extract from various candidates for entry link -->
            <xsl:variable name="entry.link"
                select="atom:link[@rel='alternate' and
                          ( @type='text/html' or
                            @type='application/xhtml+xml' )]/@href |
                            
                        l:link[@l:rel='permalink' and 
                          (@l:type='text/html' or 
                           @l:type='application/xhtml+xml')]/@rdf:resource |

                        rss09:link | rss10:link | @rdf:about | comments | 
                        link | guid[not(@isPermaLink) or @isPermaLink='true']" />

            <!-- Extract entry publish date -->
            <xsl:variable name="entry.date">
                <xsl:choose>
                    <!-- If RSS 2.0 pubDate found, perform conversion -->
                    <xsl:when test="pubDate">
                        <xsl:call-template name="rfc822_to_w3cdtf">
                            <xsl:with-param name="date" select="pubDate" />
                        </xsl:call-template>
                    </xsl:when>
                    <!-- All others assumed W3CDTF / ISO8601 -->
                    <xsl:otherwise>
                        <xsl:value-of
                            select="atom:modified | dc:date | 
                                    dcterms:modified" />
                    </xsl:otherwise> 
                </xsl:choose>
            </xsl:variable>

            <!-- Insert the appropriate feed entry format -->
            <xsl:choose> 

                <xsl:when test="$format='rss'">
                    <xsl:call-template name="rss20.entry">
                        <xsl:with-param name="entry.title" 
                            select="$entry.title" />
                        <xsl:with-param name="entry.id" 
                            select="$entry.id" />
                        <xsl:with-param name="entry.author.name" 
                            select="$entry.author.name" />
                        <xsl:with-param name="entry.author.email" 
                            select="$entry.author.email" />
                        <xsl:with-param name="entry.date" 
                            select="$entry.date" />
                        <xsl:with-param name="entry.summary" 
                            select="$entry.summary" />
                        <xsl:with-param name="entry.link" 
                            select="$entry.link" />
                    </xsl:call-template>
                </xsl:when>

                <xsl:otherwise>
                    <xsl:call-template name="atom03.entry">
                        <xsl:with-param name="entry.title" 
                            select="$entry.title" />
                        <xsl:with-param name="entry.id" 
                            select="$entry.id" />
                        <xsl:with-param name="entry.author.name" 
                            select="$entry.author.name" />
                        <xsl:with-param name="entry.author.email" 
                            select="$entry.author.email" />
                        <xsl:with-param name="entry.date" 
                            select="$entry.date" />
                        <xsl:with-param name="entry.summary" 
                            select="$entry.summary" />
                        <xsl:with-param name="entry.link" 
                            select="$entry.link" />
                    </xsl:call-template>
                </xsl:otherwise>

            </xsl:choose>

        </xsl:for-each>

    </xsl:template>
    
    <!--
        w3cdtf_to_rfc822: Accepts a date parameter in W3CDTF format,
        converts and outputs the date in RFC822 format.
    -->
    <xsl:template name="w3cdtf_to_rfc822">
        <!-- 'date' param, accepts W3CDTF format date/time -->
        <xsl:param name="date" select="'2005-04-08T04:00:00Z'" />

        <!-- Get the timezone and fixup for RFC 822 format -->
        <xsl:variable name="tz_raw"
            select="date:format-date($date, 'z')" />

        <xsl:variable name="tz">
            <xsl:choose>
                <xsl:when test="$tz_raw='UTC'">GMT</xsl:when>
                <xsl:otherwise>
                    <xsl:value-of 
                        select="concat(substring($tz_raw,4,3),
                                       substring($tz_raw,8,2) )" />
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <!-- Build the RFC 822 date/time string -->
        <xsl:value-of 
            select="concat(
            date:format-date($date, 'EEE, d MMM yyyy HH:mm:ss '), $tz)" />
    </xsl:template>
    
    <!--
        rfc822_to_w3cdtf: Accepts a date parameter in RFC822 format,
        converts and outputs the date in W3CDTF format.
    -->
    <xsl:template name="rfc822_to_w3cdtf">
        <!-- 'date' param, accepts RFC822 format date/time -->
        <!--
        <xsl:param name="date" 
            select="'Fri, 08 Apr 2005 04:00:00 GMT'" />
        -->
        <xsl:param name="date" 
            select="'Fri, 25 Mar 2005 14:12:05 -0500'" />

        <!-- Extract the month name -->
        <xsl:variable name="mn" select="substring($date, 9, 3)" />

        <!-- Map month name onto month number -->
        <xsl:variable name="m">
          <xsl:choose>
              <xsl:when test="$mn='Jan'">01</xsl:when>
              <xsl:when test="$mn='Feb'">02</xsl:when>
              <xsl:when test="$mn='Mar'">03</xsl:when>
              <xsl:when test="$mn='Apr'">04</xsl:when>
              <xsl:when test="$mn='May'">05</xsl:when>
              <xsl:when test="$mn='Jun'">06</xsl:when>
              <xsl:when test="$mn='Jul'">07</xsl:when>
              <xsl:when test="$mn='Aug'">08</xsl:when>
              <xsl:when test="$mn='Sep'">09</xsl:when>
              <xsl:when test="$mn='Oct'">10</xsl:when>
              <xsl:when test="$mn='Nov'">11</xsl:when>
              <xsl:when test="$mn='Dec'">12</xsl:when>
          </xsl:choose>
        </xsl:variable>

        <!-- Extract remaining day, year, and time from date string -->
        <xsl:variable name="d" select="substring($date, 6, 2)" />
        <xsl:variable name="y" select="substring($date, 13, 4)" />
        <xsl:variable name="hh" select="substring($date, 18, 2)" />
        <xsl:variable name="mm" select="substring($date, 21, 2)" />
        <xsl:variable name="ss" select="substring($date, 24, 2)" />
        
        <xsl:variable name="tz_raw" select="substring($date, 27)" />
        <xsl:variable name="tz">
            <xsl:choose>
                <xsl:when test="$tz_raw='GMT'">Z</xsl:when>
                <xsl:when test="$tz_raw='EDT'">-04:00</xsl:when>
                <xsl:when test="$tz_raw='EST'">-05:00</xsl:when>
                <xsl:when test="$tz_raw='CDT'">-05:00</xsl:when>
                <xsl:when test="$tz_raw='CST'">-06:00</xsl:when>
                <xsl:when test="$tz_raw='MDT'">-06:00</xsl:when>
                <xsl:when test="$tz_raw='MST'">-07:00</xsl:when>
                <xsl:when test="$tz_raw='PDT'">-07:00</xsl:when>
                <xsl:when test="$tz_raw='PST'">-08:00</xsl:when>
                <xsl:otherwise>
                    <xsl:value-of 
                        select="concat(substring($tz_raw,1,3),':',
                                       substring($tz_raw,4))" />
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <!-- Build and output the W3CDTF date from components -->
        <xsl:value-of select="concat($y,'-',$m,'-',$d, 'T',
                                     $hh,':',$mm,':',$ss, $tz)" />
    </xsl:template>

</xsl:stylesheet>
