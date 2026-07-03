<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:tei="http://www.tei-c.org/ns/1.0">
    <!--xsl:と付くタグはXSLTの命令だと解釈してという意味-->
    <!--tei:と付くタグはTEI名前空間の要素を指すと解釈してという意味-->


    <xsl:output method="html" encoding="UTF-8" indent="yes"/>


<xsl:template match="/">
    <!-- ここに変換ルールを書いていく -->
 
  <html>
    <head>
      <title>TEI to HTML: Chiune Sugihara</title>
      <style>
        body { 
            font-family: Arial; 
            max-width: 700px; 
            margin: 40px auto; 
            line-height: 1.6; 
        }

        .container {
            max-width: 800px;
            background 
        }



        .quote  { 
            font-style: italic; color: #848393; 
            font-weight: bold; 
        }

        .person { 
            font-weight: bold; color: #c0392b; 
            font-weight: bold; 
        }

        .place { 
            font-weight: bold; color: #2980b9; 
            font-weight: bold; 
        }

        .work  { 
            font-weight: bold; color: #44ad63; 
            font-weight: bold; 
        }

        .organization  { 
            font-weight: bold; color: #95ae27; 
            font-weight: bold; 
        }

        .object {
            font-weight: bold; color: #6044ad
            font-weight: bold; 
        }


  





      </style>
    </head>


    <body>
        <div class="container">
            <div class="header">
            <h1>Transformation from XMl/TEI to HTML: Chiune Sugihara</h1>
            </div>
            <xsl:apply-templates select="tei:TEI/tei:text/tei:body"/>
        </div>
    </body>
  </html>
</xsl:template>


    <!-- ★ divを透過的に処理(追加) ★ -->
    <xsl:template match="tei:div">
    <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="tei:head">
        <h2><xsl:apply-templates/></h2>
    </xsl:template>

    <xsl:template match="tei:p">
        <p><xsl:apply-templates/></p>
    </xsl:template>




    <!-- persName -->
    <xsl:template match="tei:persName">
    <span class="person"><xsl:apply-templates/></span>
    </xsl:template>


    <!-- placeName -->
    <xsl:template match="tei:placeName">
    <span class="place"><xsl:apply-templates/></span>
    </xsl:template>


    <!-- title -->
    <xsl:template match="tei:title">
    <span class="work"><xsl:apply-templates/></span>
    </xsl:template> 

    <!--OrgName-->
    <xsl:template match="tei:orgName">
    <span class="organization"><xsl:apply-templates/></span>
    </xsl:template>


    <!--object-->
    <xsl:template match="tei:rs[@type='event'] | tei:rs[@type='infrastructure'] | tei:rs[@type='concept']">
    <span class="object"><xsl:apply-templates/></span>
    </xsl:template>


</xsl:stylesheet>