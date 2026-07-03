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

        .header {
            background-color: #d6eaf8;   /* 薄い青 */
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            text-align: center;
        }


        .intro {
            background-color: #fafafa;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }

        .intro p {
            margin-top: 0;
            text-align: left;
        }


        .color-desc {
            list-style: none;
            padding: 0;
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin: 0;
        }

        .color-desc li {
            font-size: 0.9em;
        }


        body { 
            font-family: Arial; 
            margin: 0;
            line-height: 1.6; 
            background-color: #ffffff;   /* ★ ページ全体の背景(薄いグレー) */
        }

        .container {
            max-width: 700px;
            margin: 40px auto;
            background: #ffffff;          /* コンテンツは白のまま */
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);  /* ★ 影を追加 */
            border-radius: 10px;          /* 角を少し丸めると、より「カード」っぽく見える */
        }


        .section {
            background-color: #f0f0f0;   /* 薄い灰色 */
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
        }



        .quote  { 
            font-style: italic; color: #291cea; 
            font-weight: bold; 
        }

        .person { 
            font-weight: bold; 
            color: #c0392b; 
        }

        .place { 
            font-weight: bold; 
            color: #2980b9; 
        }

        .work  { 
            font-weight: bold; 
            color: #44ad63; 
        }

        .organization  { 
            font-weight: bold; 
            color: #95ae27;  
        }

        .object {
            font-weight: bold; 
            color: #b909ff;
             
        }


  





      </style>
    </head>


    <body>
    <div class="box">
        <div class="container">
            <div class="header">
            <h1>Transformation from XMl/TEI to HTML: Chiune Sugihara</h1>
            <div class="intro">
                <p>This page presents a TEI/XML-encoded text about Chiune Sugihara,
                transformed into HTML using XSLT. Entities mentioned
                in the text are highlighted below according to their type.</p>
                <ul class="color-desc">
                    <li><span class="person">Person</span>,</li>
                    <li><span class="place">Place</span>,</li>
                    <li><span class="work">Work / Title</span>,</li>
                    <li><span class="organization">Organization</span>,</li>
                    <li><span class="object">Object: Event / Concept / Infrastructure</span>,</li>
                    <li><span class="quote">Quotation</span></li>
                </ul>   
            </div>
            </div>
            <xsl:apply-templates select="tei:TEI/tei:text/tei:body"/>
            
        </div>
    </div>
    </body>
  </html>
</xsl:template>


    <!-- ★ divを透過的に処理(追加) ★ -->
    <xsl:template match="tei:div">
        <div class="section">
            <xsl:apply-templates/>
        </div>
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

    <!--quote-->
    <xsl:template match="tei:quote">
    <span class="quote"><xsl:apply-templates/></span>
    </xsl:template>


</xsl:stylesheet>