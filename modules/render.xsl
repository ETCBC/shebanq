<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
      xmlns:xs="http://www.w3.org/2001/XMLSchema"
      exclude-result-prefixes="xs"
      version="2.0">
    
    <!-- 
        ======================================== 
    -->
    
    <xsl:output method="html"/>
    
    <xsl:template match="/">
        <div class="result">
            <xsl:apply-templates select="context_list"/>
        </div>
    </xsl:template>
    
    <!-- 
        ======================================== 
    -->  
    
    <xsl:template match="context_list">
        <xsl:for-each select="context">                        
            <div class="context">
                <xsl:for-each select="context_part">
                    <div class="context-part"><span></span>
                        <xsl:for-each select="v">
                            <div class="verse">
                                <div class="book-title">
                                    <xsl:value-of select="@b"/>&#160;<xsl:value-of select="@c"/>:<xsl:value-of select="@v"/>
                                </div>
                                <div class="hebrew">
                                    <xsl:for-each select="s">
                                        <xsl:variable name="id_d" select="@id_d"/>
                                        <span class="sentence" title="id_d={$id_d}">
                                            <xsl:for-each select="w">
                                                <xsl:variable name="monad" select="round(@fm)"/>
                                                <xsl:variable name="hasfocus" select="../../../../focus[round(@first) &lt;= $monad and round(@last) &gt;= $monad][1]"/>
                                                 <xsl:choose>
                                                    <xsl:when test="$hasfocus">
                                                        <span class="word focus">
                                                            <xsl:value-of select="text()"/>
                                                        </span>
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        <span class="word">
                                                            <xsl:value-of select="text()"/>
                                                        </span>
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                                <xsl:text> </xsl:text>
                                            </xsl:for-each>
                                         </span>
                                    </xsl:for-each>
                                </div>
                            </div>
                        </xsl:for-each>
                    </div>
                </xsl:for-each>
            </div>
        </xsl:for-each>
    </xsl:template>
    
    <!-- 
        ======================================== 
    --> 

</xsl:stylesheet>
