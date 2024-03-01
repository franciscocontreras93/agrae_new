<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis symbologyReferenceScale="-1" hasScaleBasedVisibilityFlag="0" simplifyDrawingTol="1" simplifyAlgorithm="0" version="3.22.13-Białowieża" simplifyLocal="1" simplifyMaxScale="1" styleCategories="AllStyleCategories" minScale="100000000" simplifyDrawingHints="1" labelsEnabled="1" readOnly="0" maxScale="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <temporal endField="" mode="0" startExpression="" accumulate="0" fixedDuration="0" startField="" durationField="" durationUnit="min" enabled="0" limitMode="0" endExpression="">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <renderer-v2 referencescale="-1" type="RuleRenderer" enableorderby="0" symbollevels="0" forceraster="0">
    <rules key="{2867c40f-c9bf-4fbc-8671-4bd7ad19da6f}">
      <rule key="{83d5ebb9-5a0b-4112-83f4-3b6c52b2d5e0}" filter="&quot;CE&quot; >= 0.000000 AND &quot;CE&quot; &lt;= 2.000000" symbol="0" label="No salino"/>
      <rule key="{362ab9b9-8d09-4596-8031-1d9eaab19d9d}" filter="&quot;CE&quot; > 2.000000 AND &quot;CE&quot; &lt;= 4.000000" symbol="1" label="Algo salino"/>
      <rule key="{b1c31622-569e-4bc8-9b26-15355ed60841}" filter="&quot;CE&quot; > 4.000000 AND &quot;CE&quot; &lt;= 8.000000" symbol="2" label="Salino"/>
      <rule key="{ac274922-074a-4df3-a735-7321074f75ca}" filter="&quot;CE&quot; > 8.000000 AND &quot;CE&quot; &lt;= 16.000000" symbol="3" label="Muy salino"/>
      <rule key="{820b719e-511e-42b8-9d70-2096dfd54484}" filter="&quot;CE&quot; > 16.000000 AND &quot;CE&quot; &lt;= 100.000000" symbol="4" label="Intensa salino"/>
    </rules>
    <symbols>
      <symbol alpha="1" name="0" type="fill" clip_to_extent="1" force_rhr="0">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" value="" type="QString"/>
            <Option name="properties"/>
            <Option name="type" value="collection" type="QString"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" locked="0" class="SimpleFill" enabled="1">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="color" value="62,121,93,255" type="QString"/>
            <Option name="joinstyle" value="bevel" type="QString"/>
            <Option name="offset" value="0,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="0,0,0,255" type="QString"/>
            <Option name="outline_style" value="no" type="QString"/>
            <Option name="outline_width" value="0.26" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="style" value="solid" type="QString"/>
          </Option>
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="62,121,93,255" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="0,0,0,255" k="outline_color"/>
          <prop v="no" k="outline_style"/>
          <prop v="0.26" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="solid" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" name="1" type="fill" clip_to_extent="1" force_rhr="0">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" value="" type="QString"/>
            <Option name="properties"/>
            <Option name="type" value="collection" type="QString"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" locked="0" class="SimpleFill" enabled="1">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="color" value="115,200,31,255" type="QString"/>
            <Option name="joinstyle" value="bevel" type="QString"/>
            <Option name="offset" value="0,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="0,0,0,255" type="QString"/>
            <Option name="outline_style" value="no" type="QString"/>
            <Option name="outline_width" value="0.26" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="style" value="solid" type="QString"/>
          </Option>
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="115,200,31,255" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="0,0,0,255" k="outline_color"/>
          <prop v="no" k="outline_style"/>
          <prop v="0.26" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="solid" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" name="2" type="fill" clip_to_extent="1" force_rhr="0">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" value="" type="QString"/>
            <Option name="properties"/>
            <Option name="type" value="collection" type="QString"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" locked="0" class="SimpleFill" enabled="1">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="color" value="255,177,19,255" type="QString"/>
            <Option name="joinstyle" value="bevel" type="QString"/>
            <Option name="offset" value="0,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="0,0,0,255" type="QString"/>
            <Option name="outline_style" value="no" type="QString"/>
            <Option name="outline_width" value="0.26" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="style" value="solid" type="QString"/>
          </Option>
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="255,177,19,255" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="0,0,0,255" k="outline_color"/>
          <prop v="no" k="outline_style"/>
          <prop v="0.26" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="solid" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" name="3" type="fill" clip_to_extent="1" force_rhr="0">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" value="" type="QString"/>
            <Option name="properties"/>
            <Option name="type" value="collection" type="QString"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" locked="0" class="SimpleFill" enabled="1">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="color" value="234,38,24,255" type="QString"/>
            <Option name="joinstyle" value="bevel" type="QString"/>
            <Option name="offset" value="0,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="0,0,0,255" type="QString"/>
            <Option name="outline_style" value="no" type="QString"/>
            <Option name="outline_width" value="0.26" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="style" value="solid" type="QString"/>
          </Option>
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="234,38,24,255" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="0,0,0,255" k="outline_color"/>
          <prop v="no" k="outline_style"/>
          <prop v="0.26" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="solid" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" name="4" type="fill" clip_to_extent="1" force_rhr="0">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" value="" type="QString"/>
            <Option name="properties"/>
            <Option name="type" value="collection" type="QString"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" locked="0" class="SimpleFill" enabled="1">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="color" value="215,24,164,255" type="QString"/>
            <Option name="joinstyle" value="bevel" type="QString"/>
            <Option name="offset" value="0,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="0,0,0,255" type="QString"/>
            <Option name="outline_style" value="no" type="QString"/>
            <Option name="outline_width" value="0.26" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="style" value="solid" type="QString"/>
          </Option>
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="215,24,164,255" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="0,0,0,255" k="outline_color"/>
          <prop v="no" k="outline_style"/>
          <prop v="0.26" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="solid" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style fontKerning="1" fontItalic="0" fontSizeMapUnitScale="3x:0,0,0,0,0,0" textColor="50,50,50,255" fontLetterSpacing="0" fontWeight="87" legendString="Aa" fontFamily="Arial" fontWordSpacing="0" blendMode="0" useSubstitutions="0" namedStyle="Black" fontStrikeout="0" allowHtml="0" fontSize="8" fontUnderline="0" capitalization="0" isExpression="1" fontSizeUnit="Point" fieldName="round(ce,2)" textOrientation="horizontal" previewBkgrdColor="255,255,255,255" multilineHeight="1" textOpacity="1">
        <families/>
        <text-buffer bufferSize="1" bufferColor="250,250,250,255" bufferNoFill="1" bufferOpacity="1" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferBlendMode="0" bufferSizeUnits="MM" bufferJoinStyle="128" bufferDraw="1"/>
        <text-mask maskSize="0" maskJoinStyle="128" maskSizeUnits="MM" maskEnabled="0" maskOpacity="1" maskedSymbolLayers="" maskType="0" maskSizeMapUnitScale="3x:0,0,0,0,0,0"/>
        <background shapeSizeUnit="Point" shapeOffsetX="0" shapeDraw="0" shapeBorderWidth="0" shapeType="0" shapeRadiiY="0" shapeSizeY="0" shapeBlendMode="0" shapeRotation="0" shapeBorderColor="128,128,128,255" shapeJoinStyle="64" shapeOffsetY="0" shapeSizeType="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiUnit="Point" shapeOffsetUnit="Point" shapeSizeX="0" shapeOpacity="1" shapeBorderWidthUnit="Point" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeRotationType="0" shapeSVGFile="" shapeRadiiX="0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeFillColor="255,255,255,255" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0">
          <symbol alpha="1" name="markerSymbol" type="marker" clip_to_extent="1" force_rhr="0">
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" value="" type="QString"/>
                <Option name="properties"/>
                <Option name="type" value="collection" type="QString"/>
              </Option>
            </data_defined_properties>
            <layer pass="0" locked="0" class="SimpleMarker" enabled="1">
              <Option type="Map">
                <Option name="angle" value="0" type="QString"/>
                <Option name="cap_style" value="square" type="QString"/>
                <Option name="color" value="183,72,75,255" type="QString"/>
                <Option name="horizontal_anchor_point" value="1" type="QString"/>
                <Option name="joinstyle" value="bevel" type="QString"/>
                <Option name="name" value="circle" type="QString"/>
                <Option name="offset" value="0,0" type="QString"/>
                <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
                <Option name="offset_unit" value="MM" type="QString"/>
                <Option name="outline_color" value="35,35,35,255" type="QString"/>
                <Option name="outline_style" value="solid" type="QString"/>
                <Option name="outline_width" value="0" type="QString"/>
                <Option name="outline_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
                <Option name="outline_width_unit" value="MM" type="QString"/>
                <Option name="scale_method" value="diameter" type="QString"/>
                <Option name="size" value="2" type="QString"/>
                <Option name="size_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
                <Option name="size_unit" value="MM" type="QString"/>
                <Option name="vertical_anchor_point" value="1" type="QString"/>
              </Option>
              <prop v="0" k="angle"/>
              <prop v="square" k="cap_style"/>
              <prop v="183,72,75,255" k="color"/>
              <prop v="1" k="horizontal_anchor_point"/>
              <prop v="bevel" k="joinstyle"/>
              <prop v="circle" k="name"/>
              <prop v="0,0" k="offset"/>
              <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
              <prop v="MM" k="offset_unit"/>
              <prop v="35,35,35,255" k="outline_color"/>
              <prop v="solid" k="outline_style"/>
              <prop v="0" k="outline_width"/>
              <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
              <prop v="MM" k="outline_width_unit"/>
              <prop v="diameter" k="scale_method"/>
              <prop v="2" k="size"/>
              <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
              <prop v="MM" k="size_unit"/>
              <prop v="1" k="vertical_anchor_point"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" value="" type="QString"/>
                  <Option name="properties"/>
                  <Option name="type" value="collection" type="QString"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol alpha="1" name="fillSymbol" type="fill" clip_to_extent="1" force_rhr="0">
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" value="" type="QString"/>
                <Option name="properties"/>
                <Option name="type" value="collection" type="QString"/>
              </Option>
            </data_defined_properties>
            <layer pass="0" locked="0" class="SimpleFill" enabled="1">
              <Option type="Map">
                <Option name="border_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
                <Option name="color" value="255,255,255,255" type="QString"/>
                <Option name="joinstyle" value="bevel" type="QString"/>
                <Option name="offset" value="0,0" type="QString"/>
                <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
                <Option name="offset_unit" value="MM" type="QString"/>
                <Option name="outline_color" value="128,128,128,255" type="QString"/>
                <Option name="outline_style" value="no" type="QString"/>
                <Option name="outline_width" value="0" type="QString"/>
                <Option name="outline_width_unit" value="Point" type="QString"/>
                <Option name="style" value="solid" type="QString"/>
              </Option>
              <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
              <prop v="255,255,255,255" k="color"/>
              <prop v="bevel" k="joinstyle"/>
              <prop v="0,0" k="offset"/>
              <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
              <prop v="MM" k="offset_unit"/>
              <prop v="128,128,128,255" k="outline_color"/>
              <prop v="no" k="outline_style"/>
              <prop v="0" k="outline_width"/>
              <prop v="Point" k="outline_width_unit"/>
              <prop v="solid" k="style"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" value="" type="QString"/>
                  <Option name="properties"/>
                  <Option name="type" value="collection" type="QString"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </background>
        <shadow shadowRadiusAlphaOnly="0" shadowRadius="1.5" shadowScale="100" shadowOffsetAngle="135" shadowColor="0,0,0,255" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowUnder="0" shadowOffsetDist="1" shadowOpacity="0.69999999999999996" shadowBlendMode="6" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetUnit="MM" shadowOffsetGlobal="1" shadowRadiusUnit="MM" shadowDraw="0"/>
        <dd_properties>
          <Option type="Map">
            <Option name="name" value="" type="QString"/>
            <Option name="properties"/>
            <Option name="type" value="collection" type="QString"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format multilineAlign="3" autoWrapLength="0" decimals="3" leftDirectionSymbol="&lt;" rightDirectionSymbol=">" placeDirectionSymbol="0" plussign="0" reverseDirectionSymbol="0" addDirectionSymbol="0" formatNumbers="0" wrapChar="" useMaxLineLengthForAutoWrap="1"/>
      <placement polygonPlacementFlags="2" preserveRotation="1" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" maxCurvedCharAngleIn="25" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" centroidInside="1" lineAnchorPercent="0.5" offsetUnits="MM" quadOffset="4" priority="5" centroidWhole="0" overrunDistance="0" geometryGeneratorType="PointGeometry" overrunDistanceUnit="MM" placementFlags="10" repeatDistance="0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" layerType="PolygonGeometry" distUnits="MM" dist="0" fitInPolygonOnly="0" yOffset="0" geometryGenerator="" xOffset="0" maxCurvedCharAngleOut="-25" distMapUnitScale="3x:0,0,0,0,0,0" rotationUnit="AngleDegrees" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" lineAnchorType="0" geometryGeneratorEnabled="0" rotationAngle="0" offsetType="0" placement="0" lineAnchorClipping="0" repeatDistanceUnits="MM"/>
      <rendering scaleVisibility="0" drawLabels="1" scaleMax="0" obstacleType="1" fontLimitPixelSize="0" labelPerPart="0" fontMinPixelSize="3" limitNumLabels="0" scaleMin="0" fontMaxPixelSize="10000" minFeatureSize="0" mergeLines="0" zIndex="0" upsidedownLabels="0" obstacleFactor="1" unplacedVisibility="0" obstacle="1" displayAll="0" maxNumLabels="2000"/>
      <dd_properties>
        <Option type="Map">
          <Option name="name" value="" type="QString"/>
          <Option name="properties"/>
          <Option name="type" value="collection" type="QString"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option name="anchorPoint" value="pole_of_inaccessibility" type="QString"/>
          <Option name="blendMode" value="0" type="int"/>
          <Option name="ddProperties" type="Map">
            <Option name="name" value="" type="QString"/>
            <Option name="properties"/>
            <Option name="type" value="collection" type="QString"/>
          </Option>
          <Option name="drawToAllParts" value="false" type="bool"/>
          <Option name="enabled" value="0" type="QString"/>
          <Option name="labelAnchorPoint" value="point_on_exterior" type="QString"/>
          <Option name="lineSymbol" value="&lt;symbol alpha=&quot;1&quot; name=&quot;symbol&quot; type=&quot;line&quot; clip_to_extent=&quot;1&quot; force_rhr=&quot;0&quot;>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;name&quot; value=&quot;&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option name=&quot;type&quot; value=&quot;collection&quot; type=&quot;QString&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;layer pass=&quot;0&quot; locked=&quot;0&quot; class=&quot;SimpleLine&quot; enabled=&quot;1&quot;>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;align_dash_pattern&quot; value=&quot;0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;capstyle&quot; value=&quot;square&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;customdash&quot; value=&quot;5;2&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;customdash_map_unit_scale&quot; value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;customdash_unit&quot; value=&quot;MM&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;dash_pattern_offset&quot; value=&quot;0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;dash_pattern_offset_map_unit_scale&quot; value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;dash_pattern_offset_unit&quot; value=&quot;MM&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;draw_inside_polygon&quot; value=&quot;0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;joinstyle&quot; value=&quot;bevel&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;line_color&quot; value=&quot;60,60,60,255&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;line_style&quot; value=&quot;solid&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;line_width&quot; value=&quot;0.3&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;line_width_unit&quot; value=&quot;MM&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;offset&quot; value=&quot;0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;offset_map_unit_scale&quot; value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;offset_unit&quot; value=&quot;MM&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;ring_filter&quot; value=&quot;0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;trim_distance_end&quot; value=&quot;0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;trim_distance_end_map_unit_scale&quot; value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;trim_distance_end_unit&quot; value=&quot;MM&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;trim_distance_start&quot; value=&quot;0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;trim_distance_start_map_unit_scale&quot; value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;trim_distance_start_unit&quot; value=&quot;MM&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;tweak_dash_pattern_on_corners&quot; value=&quot;0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;use_custom_dash&quot; value=&quot;0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;width_map_unit_scale&quot; value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot;/>&lt;/Option>&lt;prop v=&quot;0&quot; k=&quot;align_dash_pattern&quot;/>&lt;prop v=&quot;square&quot; k=&quot;capstyle&quot;/>&lt;prop v=&quot;5;2&quot; k=&quot;customdash&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;customdash_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;customdash_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;dash_pattern_offset&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;dash_pattern_offset_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;dash_pattern_offset_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;draw_inside_polygon&quot;/>&lt;prop v=&quot;bevel&quot; k=&quot;joinstyle&quot;/>&lt;prop v=&quot;60,60,60,255&quot; k=&quot;line_color&quot;/>&lt;prop v=&quot;solid&quot; k=&quot;line_style&quot;/>&lt;prop v=&quot;0.3&quot; k=&quot;line_width&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;line_width_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;offset&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;offset_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;offset_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;ring_filter&quot;/>&lt;prop v=&quot;0&quot; k=&quot;trim_distance_end&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;trim_distance_end_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;trim_distance_end_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;trim_distance_start&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;trim_distance_start_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;trim_distance_start_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;tweak_dash_pattern_on_corners&quot;/>&lt;prop v=&quot;0&quot; k=&quot;use_custom_dash&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;width_map_unit_scale&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;name&quot; value=&quot;&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option name=&quot;type&quot; value=&quot;collection&quot; type=&quot;QString&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>" type="QString"/>
          <Option name="minLength" value="0" type="double"/>
          <Option name="minLengthMapUnitScale" value="3x:0,0,0,0,0,0" type="QString"/>
          <Option name="minLengthUnit" value="MM" type="QString"/>
          <Option name="offsetFromAnchor" value="0" type="double"/>
          <Option name="offsetFromAnchorMapUnitScale" value="3x:0,0,0,0,0,0" type="QString"/>
          <Option name="offsetFromAnchorUnit" value="MM" type="QString"/>
          <Option name="offsetFromLabel" value="0" type="double"/>
          <Option name="offsetFromLabelMapUnitScale" value="3x:0,0,0,0,0,0" type="QString"/>
          <Option name="offsetFromLabelUnit" value="MM" type="QString"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <customproperties>
    <Option type="Map">
      <Option name="QFieldSync/action" value="offline" type="QString"/>
      <Option name="QFieldSync/cloud_action" value="offline" type="QString"/>
      <Option name="QFieldSync/photo_naming" value="{}" type="QString"/>
      <Option name="dualview/previewExpressions" type="List">
        <Option value="lote || '-' ||segmento" type="QString"/>
      </Option>
      <Option name="embeddedWidgets/count" value="0" type="QString"/>
      <Option name="subset_expression" value="&quot;idlotecampania&quot; in (366, 371, 361, 368, 370, 363, 362, 369, 367)" type="QString"/>
      <Option name="subset_expression_checked" value="0" type="int"/>
      <Option name="variableNames"/>
      <Option name="variableValues"/>
    </Option>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>0.7</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory lineSizeType="MM" spacingUnit="MM" lineSizeScale="3x:0,0,0,0,0,0" penAlpha="255" barWidth="5" height="15" sizeScale="3x:0,0,0,0,0,0" backgroundAlpha="255" opacity="1" rotationOffset="270" showAxis="0" spacingUnitScale="3x:0,0,0,0,0,0" enabled="0" diagramOrientation="Up" labelPlacementMethod="XHeight" penWidth="0" sizeType="MM" minimumSize="0" minScaleDenominator="0" width="15" spacing="0" direction="1" scaleBasedVisibility="0" penColor="#000000" scaleDependency="Area" maxScaleDenominator="1e+08" backgroundColor="#ffffff">
      <fontProperties description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0" style=""/>
      <attribute colorOpacity="1" field="" label="" color="#000000"/>
      <axisSymbol>
        <symbol alpha="1" name="" type="line" clip_to_extent="1" force_rhr="0">
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="0" locked="0" class="SimpleLine" enabled="1">
            <Option type="Map">
              <Option name="align_dash_pattern" value="0" type="QString"/>
              <Option name="capstyle" value="square" type="QString"/>
              <Option name="customdash" value="5;2" type="QString"/>
              <Option name="customdash_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
              <Option name="customdash_unit" value="MM" type="QString"/>
              <Option name="dash_pattern_offset" value="0" type="QString"/>
              <Option name="dash_pattern_offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
              <Option name="dash_pattern_offset_unit" value="MM" type="QString"/>
              <Option name="draw_inside_polygon" value="0" type="QString"/>
              <Option name="joinstyle" value="bevel" type="QString"/>
              <Option name="line_color" value="35,35,35,255" type="QString"/>
              <Option name="line_style" value="solid" type="QString"/>
              <Option name="line_width" value="0.26" type="QString"/>
              <Option name="line_width_unit" value="MM" type="QString"/>
              <Option name="offset" value="0" type="QString"/>
              <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
              <Option name="offset_unit" value="MM" type="QString"/>
              <Option name="ring_filter" value="0" type="QString"/>
              <Option name="trim_distance_end" value="0" type="QString"/>
              <Option name="trim_distance_end_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
              <Option name="trim_distance_end_unit" value="MM" type="QString"/>
              <Option name="trim_distance_start" value="0" type="QString"/>
              <Option name="trim_distance_start_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
              <Option name="trim_distance_start_unit" value="MM" type="QString"/>
              <Option name="tweak_dash_pattern_on_corners" value="0" type="QString"/>
              <Option name="use_custom_dash" value="0" type="QString"/>
              <Option name="width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            </Option>
            <prop v="0" k="align_dash_pattern"/>
            <prop v="square" k="capstyle"/>
            <prop v="5;2" k="customdash"/>
            <prop v="3x:0,0,0,0,0,0" k="customdash_map_unit_scale"/>
            <prop v="MM" k="customdash_unit"/>
            <prop v="0" k="dash_pattern_offset"/>
            <prop v="3x:0,0,0,0,0,0" k="dash_pattern_offset_map_unit_scale"/>
            <prop v="MM" k="dash_pattern_offset_unit"/>
            <prop v="0" k="draw_inside_polygon"/>
            <prop v="bevel" k="joinstyle"/>
            <prop v="35,35,35,255" k="line_color"/>
            <prop v="solid" k="line_style"/>
            <prop v="0.26" k="line_width"/>
            <prop v="MM" k="line_width_unit"/>
            <prop v="0" k="offset"/>
            <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
            <prop v="MM" k="offset_unit"/>
            <prop v="0" k="ring_filter"/>
            <prop v="0" k="trim_distance_end"/>
            <prop v="3x:0,0,0,0,0,0" k="trim_distance_end_map_unit_scale"/>
            <prop v="MM" k="trim_distance_end_unit"/>
            <prop v="0" k="trim_distance_start"/>
            <prop v="3x:0,0,0,0,0,0" k="trim_distance_start_map_unit_scale"/>
            <prop v="MM" k="trim_distance_start_unit"/>
            <prop v="0" k="tweak_dash_pattern_on_corners"/>
            <prop v="0" k="use_custom_dash"/>
            <prop v="3x:0,0,0,0,0,0" k="width_map_unit_scale"/>
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" value="" type="QString"/>
                <Option name="properties"/>
                <Option name="type" value="collection" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
      </axisSymbol>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings showAll="1" zIndex="0" placement="1" obstacle="0" priority="0" dist="0" linePlacementFlags="18">
    <properties>
      <Option type="Map">
        <Option name="name" value="" type="QString"/>
        <Option name="properties"/>
        <Option name="type" value="collection" type="QString"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
    <activeChecks/>
    <checkConfiguration type="Map">
      <Option name="QgsGeometryGapCheck" type="Map">
        <Option name="allowedGapsBuffer" value="0" type="double"/>
        <Option name="allowedGapsEnabled" value="false" type="bool"/>
        <Option name="allowedGapsLayer" value="" type="QString"/>
      </Option>
    </checkConfiguration>
  </geometryOptions>
  <legend showLabelLegend="0" type="default-vector"/>
  <referencedLayers/>
  <fieldConfiguration>
    <field name="id" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="ce" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias name="" index="0" field="id"/>
    <alias name="" index="1" field="ce"/>
  </aliases>
  <defaults>
    <default expression="" applyOnUpdate="0" field="id"/>
    <default expression="" applyOnUpdate="0" field="ce"/>
  </defaults>
  <constraints>
    <constraint constraints="3" exp_strength="0" notnull_strength="1" field="id" unique_strength="1"/>
    <constraint constraints="0" exp_strength="0" notnull_strength="0" field="ce" unique_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint exp="" desc="" field="id"/>
    <constraint exp="" desc="" field="ce"/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortExpression="&quot;cod_control&quot;" sortOrder="0">
    <columns>
      <column type="actions" width="-1" hidden="1"/>
      <column name="ce" type="field" width="-1" hidden="0"/>
      <column name="id" type="field" width="100" hidden="0"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <storedexpressions/>
  <editform tolerant="1"></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[# -*- codificación: utf-8 -*-
"""
Los formularios de QGIS pueden tener una función de Python que
es llamada cuando se abre el formulario.

Use esta función para añadir lógica extra a sus formularios.

Introduzca el nombre de la función en el campo
"Python Init function".
Sigue un ejemplo:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field name="AL" editable="1"/>
    <field name="AREA" editable="1"/>
    <field name="ATLAS" editable="1"/>
    <field name="ATLAS_2" editable="1"/>
    <field name="B" editable="1"/>
    <field name="BIOMASA" editable="1"/>
    <field name="CA" editable="1"/>
    <field name="CALIZA" editable="1"/>
    <field name="CARBON" editable="1"/>
    <field name="CARB_LABEL" editable="1"/>
    <field name="CARB_NIVEL" editable="1"/>
    <field name="CAR_NIVELT" editable="1"/>
    <field name="CA_EQ" editable="1"/>
    <field name="CA_F" editable="1"/>
    <field name="CE" editable="1"/>
    <field name="CE_LABEL" editable="1"/>
    <field name="CE_NIVEL" editable="1"/>
    <field name="CE_NIVELTE" editable="1"/>
    <field name="CEap" editable="1"/>
    <field name="CIC" editable="1"/>
    <field name="COB01" editable="1"/>
    <field name="COB02" editable="1"/>
    <field name="COD" editable="1"/>
    <field name="CODTEXT" editable="1"/>
    <field name="COSECHA" editable="1"/>
    <field name="COX" editable="1"/>
    <field name="CU" editable="1"/>
    <field name="CULTIVO_0" editable="1"/>
    <field name="CULTIVO_1" editable="1"/>
    <field name="EST_RESIDU" editable="1"/>
    <field name="FE" editable="1"/>
    <field name="FIRST_ATLA" editable="1"/>
    <field name="FONDO" editable="1"/>
    <field name="F_COB01" editable="1"/>
    <field name="F_COB02" editable="1"/>
    <field name="F_FONDO" editable="1"/>
    <field name="GUIA" editable="1"/>
    <field name="INDREPR" editable="1"/>
    <field name="K" editable="1"/>
    <field name="K_APORT" editable="1"/>
    <field name="K_ECOSECH" editable="1"/>
    <field name="K_EQ" editable="1"/>
    <field name="K_ERESI" editable="1"/>
    <field name="K_F" editable="1"/>
    <field name="K_INC" editable="1"/>
    <field name="K_LABEL" editable="1"/>
    <field name="K_NECESID" editable="1"/>
    <field name="K_NIVEL" editable="1"/>
    <field name="K_NIVELTEX" editable="1"/>
    <field name="Kf" editable="1"/>
    <field name="MG" editable="1"/>
    <field name="MG_EQ" editable="1"/>
    <field name="MG_F" editable="1"/>
    <field name="MN" editable="1"/>
    <field name="MO" editable="1"/>
    <field name="N" editable="1"/>
    <field name="NA" editable="1"/>
    <field name="NAME_PARC" editable="1"/>
    <field name="NA_EQ" editable="1"/>
    <field name="NA_F" editable="1"/>
    <field name="NN" editable="1"/>
    <field name="NOMBRE_AGR" editable="1"/>
    <field name="N_APORT" editable="1"/>
    <field name="N_ECOSECH" editable="1"/>
    <field name="N_ERESI" editable="1"/>
    <field name="N_INC" editable="1"/>
    <field name="N_LABEL" editable="1"/>
    <field name="N_NECESID" editable="1"/>
    <field name="N_NIVEL" editable="1"/>
    <field name="N_NIVELTEX" editable="1"/>
    <field name="OBJ" editable="1"/>
    <field name="OBJECTID" editable="1"/>
    <field name="OBJ_SEGM" editable="1"/>
    <field name="ORGANICA" editable="1"/>
    <field name="ORIG_FID" editable="1"/>
    <field name="P" editable="1"/>
    <field name="PH" editable="1"/>
    <field name="PH_LABEL" editable="1"/>
    <field name="PH_NIVEL" editable="1"/>
    <field name="PH_NIVELTE" editable="1"/>
    <field name="P_APORT" editable="1"/>
    <field name="P_ECOSECH" editable="1"/>
    <field name="P_ERESI" editable="1"/>
    <field name="P_INC" editable="1"/>
    <field name="P_LABEL" editable="1"/>
    <field name="P_NECESID" editable="1"/>
    <field name="P_NIVEL" editable="1"/>
    <field name="P_NIVELTEX" editable="1"/>
    <field name="REF_SERIE" editable="1"/>
    <field name="REL_CN" editable="1"/>
    <field name="RESIDUO" editable="1"/>
    <field name="S" editable="1"/>
    <field name="SEGM" editable="1"/>
    <field name="SERIE" editable="1"/>
    <field name="Shape_Area" editable="1"/>
    <field name="Shape_Leng" editable="1"/>
    <field name="TEXTURA" editable="1"/>
    <field name="ZN" editable="1"/>
    <field name="al" editable="1"/>
    <field name="arcilla" editable="1"/>
    <field name="arena" editable="1"/>
    <field name="as" editable="1"/>
    <field name="b" editable="1"/>
    <field name="biomasa" editable="1"/>
    <field name="ca" editable="1"/>
    <field name="ca_eq" editable="1"/>
    <field name="ca_f" editable="1"/>
    <field name="ca_inc" editable="1"/>
    <field name="ca_tipo" editable="1"/>
    <field name="caliza" editable="1"/>
    <field name="caliza_tipo" editable="1"/>
    <field name="carb_tipo" editable="1"/>
    <field name="carbonatos" editable="1"/>
    <field name="ce" editable="1"/>
    <field name="ce_influencia" editable="1"/>
    <field name="ce_tipo" editable="1"/>
    <field name="ceap" editable="1"/>
    <field name="cic" editable="1"/>
    <field name="cic_caso" editable="1"/>
    <field name="cic_tipo" editable="1"/>
    <field name="co" editable="1"/>
    <field name="cod_control" editable="1"/>
    <field name="cod_muestra" editable="1"/>
    <field name="cox" editable="1"/>
    <field name="cr" editable="1"/>
    <field name="cu" editable="1"/>
    <field name="cultivo" editable="1"/>
    <field name="exp_nombre" editable="1"/>
    <field name="fe" editable="1"/>
    <field name="fechasiembra" editable="1"/>
    <field name="g_suelo" editable="1"/>
    <field name="id" editable="1"/>
    <field name="idanalitica" editable="1"/>
    <field name="idexp" editable="1"/>
    <field name="idlotecampania" editable="1"/>
    <field name="idsegmento" editable="1"/>
    <field name="idsegmentoanalisis" editable="1"/>
    <field name="k" editable="1"/>
    <field name="k_eq" editable="1"/>
    <field name="k_f" editable="1"/>
    <field name="k_inc" editable="1"/>
    <field name="k_tipo" editable="1"/>
    <field name="layer" editable="1"/>
    <field name="limo" editable="1"/>
    <field name="lote" editable="1"/>
    <field name="mg" editable="1"/>
    <field name="mg_eq" editable="1"/>
    <field name="mg_f" editable="1"/>
    <field name="mg_inc" editable="1"/>
    <field name="mg_tipo" editable="1"/>
    <field name="mn" editable="1"/>
    <field name="mo" editable="1"/>
    <field name="n" editable="1"/>
    <field name="n_inc" editable="1"/>
    <field name="n_tipo" editable="1"/>
    <field name="na" editable="1"/>
    <field name="na_eq" editable="1"/>
    <field name="na_f" editable="1"/>
    <field name="na_inc" editable="1"/>
    <field name="na_tipo" editable="1"/>
    <field name="ni" editable="1"/>
    <field name="organi" editable="1"/>
    <field name="p" editable="1"/>
    <field name="p_inc" editable="1"/>
    <field name="p_metodo" editable="1"/>
    <field name="p_tipo" editable="1"/>
    <field name="path" editable="1"/>
    <field name="pb" editable="1"/>
    <field name="ph" editable="1"/>
    <field name="ph_tipo" editable="1"/>
    <field name="pk_uid" editable="1"/>
    <field name="prod_esperada" editable="1"/>
    <field name="regimen" editable="1"/>
    <field name="rel_cn" editable="1"/>
    <field name="residuo" editable="1"/>
    <field name="s" editable="1"/>
    <field name="segmento" editable="1"/>
    <field name="suelo" editable="1"/>
    <field name="ti" editable="1"/>
    <field name="zn" editable="1"/>
  </editable>
  <labelOnTop>
    <field name="AL" labelOnTop="0"/>
    <field name="AREA" labelOnTop="0"/>
    <field name="ATLAS" labelOnTop="0"/>
    <field name="ATLAS_2" labelOnTop="0"/>
    <field name="B" labelOnTop="0"/>
    <field name="BIOMASA" labelOnTop="0"/>
    <field name="CA" labelOnTop="0"/>
    <field name="CALIZA" labelOnTop="0"/>
    <field name="CARBON" labelOnTop="0"/>
    <field name="CARB_LABEL" labelOnTop="0"/>
    <field name="CARB_NIVEL" labelOnTop="0"/>
    <field name="CAR_NIVELT" labelOnTop="0"/>
    <field name="CA_EQ" labelOnTop="0"/>
    <field name="CA_F" labelOnTop="0"/>
    <field name="CE" labelOnTop="0"/>
    <field name="CE_LABEL" labelOnTop="0"/>
    <field name="CE_NIVEL" labelOnTop="0"/>
    <field name="CE_NIVELTE" labelOnTop="0"/>
    <field name="CEap" labelOnTop="0"/>
    <field name="CIC" labelOnTop="0"/>
    <field name="COB01" labelOnTop="0"/>
    <field name="COB02" labelOnTop="0"/>
    <field name="COD" labelOnTop="0"/>
    <field name="CODTEXT" labelOnTop="0"/>
    <field name="COSECHA" labelOnTop="0"/>
    <field name="COX" labelOnTop="0"/>
    <field name="CU" labelOnTop="0"/>
    <field name="CULTIVO_0" labelOnTop="0"/>
    <field name="CULTIVO_1" labelOnTop="0"/>
    <field name="EST_RESIDU" labelOnTop="0"/>
    <field name="FE" labelOnTop="0"/>
    <field name="FIRST_ATLA" labelOnTop="0"/>
    <field name="FONDO" labelOnTop="0"/>
    <field name="F_COB01" labelOnTop="0"/>
    <field name="F_COB02" labelOnTop="0"/>
    <field name="F_FONDO" labelOnTop="0"/>
    <field name="GUIA" labelOnTop="0"/>
    <field name="INDREPR" labelOnTop="0"/>
    <field name="K" labelOnTop="0"/>
    <field name="K_APORT" labelOnTop="0"/>
    <field name="K_ECOSECH" labelOnTop="0"/>
    <field name="K_EQ" labelOnTop="0"/>
    <field name="K_ERESI" labelOnTop="0"/>
    <field name="K_F" labelOnTop="0"/>
    <field name="K_INC" labelOnTop="0"/>
    <field name="K_LABEL" labelOnTop="0"/>
    <field name="K_NECESID" labelOnTop="0"/>
    <field name="K_NIVEL" labelOnTop="0"/>
    <field name="K_NIVELTEX" labelOnTop="0"/>
    <field name="Kf" labelOnTop="0"/>
    <field name="MG" labelOnTop="0"/>
    <field name="MG_EQ" labelOnTop="0"/>
    <field name="MG_F" labelOnTop="0"/>
    <field name="MN" labelOnTop="0"/>
    <field name="MO" labelOnTop="0"/>
    <field name="N" labelOnTop="0"/>
    <field name="NA" labelOnTop="0"/>
    <field name="NAME_PARC" labelOnTop="0"/>
    <field name="NA_EQ" labelOnTop="0"/>
    <field name="NA_F" labelOnTop="0"/>
    <field name="NN" labelOnTop="0"/>
    <field name="NOMBRE_AGR" labelOnTop="0"/>
    <field name="N_APORT" labelOnTop="0"/>
    <field name="N_ECOSECH" labelOnTop="0"/>
    <field name="N_ERESI" labelOnTop="0"/>
    <field name="N_INC" labelOnTop="0"/>
    <field name="N_LABEL" labelOnTop="0"/>
    <field name="N_NECESID" labelOnTop="0"/>
    <field name="N_NIVEL" labelOnTop="0"/>
    <field name="N_NIVELTEX" labelOnTop="0"/>
    <field name="OBJ" labelOnTop="0"/>
    <field name="OBJECTID" labelOnTop="0"/>
    <field name="OBJ_SEGM" labelOnTop="0"/>
    <field name="ORGANICA" labelOnTop="0"/>
    <field name="ORIG_FID" labelOnTop="0"/>
    <field name="P" labelOnTop="0"/>
    <field name="PH" labelOnTop="0"/>
    <field name="PH_LABEL" labelOnTop="0"/>
    <field name="PH_NIVEL" labelOnTop="0"/>
    <field name="PH_NIVELTE" labelOnTop="0"/>
    <field name="P_APORT" labelOnTop="0"/>
    <field name="P_ECOSECH" labelOnTop="0"/>
    <field name="P_ERESI" labelOnTop="0"/>
    <field name="P_INC" labelOnTop="0"/>
    <field name="P_LABEL" labelOnTop="0"/>
    <field name="P_NECESID" labelOnTop="0"/>
    <field name="P_NIVEL" labelOnTop="0"/>
    <field name="P_NIVELTEX" labelOnTop="0"/>
    <field name="REF_SERIE" labelOnTop="0"/>
    <field name="REL_CN" labelOnTop="0"/>
    <field name="RESIDUO" labelOnTop="0"/>
    <field name="S" labelOnTop="0"/>
    <field name="SEGM" labelOnTop="0"/>
    <field name="SERIE" labelOnTop="0"/>
    <field name="Shape_Area" labelOnTop="0"/>
    <field name="Shape_Leng" labelOnTop="0"/>
    <field name="TEXTURA" labelOnTop="0"/>
    <field name="ZN" labelOnTop="0"/>
    <field name="al" labelOnTop="0"/>
    <field name="arcilla" labelOnTop="0"/>
    <field name="arena" labelOnTop="0"/>
    <field name="as" labelOnTop="0"/>
    <field name="b" labelOnTop="0"/>
    <field name="biomasa" labelOnTop="0"/>
    <field name="ca" labelOnTop="0"/>
    <field name="ca_eq" labelOnTop="0"/>
    <field name="ca_f" labelOnTop="0"/>
    <field name="ca_inc" labelOnTop="0"/>
    <field name="ca_tipo" labelOnTop="0"/>
    <field name="caliza" labelOnTop="0"/>
    <field name="caliza_tipo" labelOnTop="0"/>
    <field name="carb_tipo" labelOnTop="0"/>
    <field name="carbonatos" labelOnTop="0"/>
    <field name="ce" labelOnTop="0"/>
    <field name="ce_influencia" labelOnTop="0"/>
    <field name="ce_tipo" labelOnTop="0"/>
    <field name="ceap" labelOnTop="0"/>
    <field name="cic" labelOnTop="0"/>
    <field name="cic_caso" labelOnTop="0"/>
    <field name="cic_tipo" labelOnTop="0"/>
    <field name="co" labelOnTop="0"/>
    <field name="cod_control" labelOnTop="0"/>
    <field name="cod_muestra" labelOnTop="0"/>
    <field name="cox" labelOnTop="0"/>
    <field name="cr" labelOnTop="0"/>
    <field name="cu" labelOnTop="0"/>
    <field name="cultivo" labelOnTop="0"/>
    <field name="exp_nombre" labelOnTop="0"/>
    <field name="fe" labelOnTop="0"/>
    <field name="fechasiembra" labelOnTop="0"/>
    <field name="g_suelo" labelOnTop="0"/>
    <field name="id" labelOnTop="0"/>
    <field name="idanalitica" labelOnTop="0"/>
    <field name="idexp" labelOnTop="0"/>
    <field name="idlotecampania" labelOnTop="0"/>
    <field name="idsegmento" labelOnTop="0"/>
    <field name="idsegmentoanalisis" labelOnTop="0"/>
    <field name="k" labelOnTop="0"/>
    <field name="k_eq" labelOnTop="0"/>
    <field name="k_f" labelOnTop="0"/>
    <field name="k_inc" labelOnTop="0"/>
    <field name="k_tipo" labelOnTop="0"/>
    <field name="layer" labelOnTop="0"/>
    <field name="limo" labelOnTop="0"/>
    <field name="lote" labelOnTop="0"/>
    <field name="mg" labelOnTop="0"/>
    <field name="mg_eq" labelOnTop="0"/>
    <field name="mg_f" labelOnTop="0"/>
    <field name="mg_inc" labelOnTop="0"/>
    <field name="mg_tipo" labelOnTop="0"/>
    <field name="mn" labelOnTop="0"/>
    <field name="mo" labelOnTop="0"/>
    <field name="n" labelOnTop="0"/>
    <field name="n_inc" labelOnTop="0"/>
    <field name="n_tipo" labelOnTop="0"/>
    <field name="na" labelOnTop="0"/>
    <field name="na_eq" labelOnTop="0"/>
    <field name="na_f" labelOnTop="0"/>
    <field name="na_inc" labelOnTop="0"/>
    <field name="na_tipo" labelOnTop="0"/>
    <field name="ni" labelOnTop="0"/>
    <field name="organi" labelOnTop="0"/>
    <field name="p" labelOnTop="0"/>
    <field name="p_inc" labelOnTop="0"/>
    <field name="p_metodo" labelOnTop="0"/>
    <field name="p_tipo" labelOnTop="0"/>
    <field name="path" labelOnTop="0"/>
    <field name="pb" labelOnTop="0"/>
    <field name="ph" labelOnTop="0"/>
    <field name="ph_tipo" labelOnTop="0"/>
    <field name="pk_uid" labelOnTop="0"/>
    <field name="prod_esperada" labelOnTop="0"/>
    <field name="regimen" labelOnTop="0"/>
    <field name="rel_cn" labelOnTop="0"/>
    <field name="residuo" labelOnTop="0"/>
    <field name="s" labelOnTop="0"/>
    <field name="segmento" labelOnTop="0"/>
    <field name="suelo" labelOnTop="0"/>
    <field name="ti" labelOnTop="0"/>
    <field name="zn" labelOnTop="0"/>
  </labelOnTop>
  <reuseLastValue>
    <field name="al" reuseLastValue="0"/>
    <field name="arcilla" reuseLastValue="0"/>
    <field name="arena" reuseLastValue="0"/>
    <field name="as" reuseLastValue="0"/>
    <field name="b" reuseLastValue="0"/>
    <field name="biomasa" reuseLastValue="0"/>
    <field name="ca" reuseLastValue="0"/>
    <field name="ca_eq" reuseLastValue="0"/>
    <field name="ca_f" reuseLastValue="0"/>
    <field name="ca_inc" reuseLastValue="0"/>
    <field name="ca_tipo" reuseLastValue="0"/>
    <field name="caliza" reuseLastValue="0"/>
    <field name="caliza_tipo" reuseLastValue="0"/>
    <field name="carb_tipo" reuseLastValue="0"/>
    <field name="carbonatos" reuseLastValue="0"/>
    <field name="ce" reuseLastValue="0"/>
    <field name="ce_influencia" reuseLastValue="0"/>
    <field name="ce_tipo" reuseLastValue="0"/>
    <field name="ceap" reuseLastValue="0"/>
    <field name="cic" reuseLastValue="0"/>
    <field name="cic_caso" reuseLastValue="0"/>
    <field name="cic_tipo" reuseLastValue="0"/>
    <field name="co" reuseLastValue="0"/>
    <field name="cod_control" reuseLastValue="0"/>
    <field name="cod_muestra" reuseLastValue="0"/>
    <field name="cox" reuseLastValue="0"/>
    <field name="cr" reuseLastValue="0"/>
    <field name="cu" reuseLastValue="0"/>
    <field name="cultivo" reuseLastValue="0"/>
    <field name="exp_nombre" reuseLastValue="0"/>
    <field name="fe" reuseLastValue="0"/>
    <field name="fechasiembra" reuseLastValue="0"/>
    <field name="g_suelo" reuseLastValue="0"/>
    <field name="id" reuseLastValue="0"/>
    <field name="idanalitica" reuseLastValue="0"/>
    <field name="idexp" reuseLastValue="0"/>
    <field name="idlotecampania" reuseLastValue="0"/>
    <field name="idsegmento" reuseLastValue="0"/>
    <field name="idsegmentoanalisis" reuseLastValue="0"/>
    <field name="k" reuseLastValue="0"/>
    <field name="k_eq" reuseLastValue="0"/>
    <field name="k_f" reuseLastValue="0"/>
    <field name="k_inc" reuseLastValue="0"/>
    <field name="k_tipo" reuseLastValue="0"/>
    <field name="limo" reuseLastValue="0"/>
    <field name="lote" reuseLastValue="0"/>
    <field name="mg" reuseLastValue="0"/>
    <field name="mg_eq" reuseLastValue="0"/>
    <field name="mg_f" reuseLastValue="0"/>
    <field name="mg_inc" reuseLastValue="0"/>
    <field name="mg_tipo" reuseLastValue="0"/>
    <field name="mn" reuseLastValue="0"/>
    <field name="mo" reuseLastValue="0"/>
    <field name="n" reuseLastValue="0"/>
    <field name="n_inc" reuseLastValue="0"/>
    <field name="n_tipo" reuseLastValue="0"/>
    <field name="na" reuseLastValue="0"/>
    <field name="na_eq" reuseLastValue="0"/>
    <field name="na_f" reuseLastValue="0"/>
    <field name="na_inc" reuseLastValue="0"/>
    <field name="na_tipo" reuseLastValue="0"/>
    <field name="ni" reuseLastValue="0"/>
    <field name="organi" reuseLastValue="0"/>
    <field name="p" reuseLastValue="0"/>
    <field name="p_inc" reuseLastValue="0"/>
    <field name="p_metodo" reuseLastValue="0"/>
    <field name="p_tipo" reuseLastValue="0"/>
    <field name="pb" reuseLastValue="0"/>
    <field name="ph" reuseLastValue="0"/>
    <field name="ph_tipo" reuseLastValue="0"/>
    <field name="prod_esperada" reuseLastValue="0"/>
    <field name="regimen" reuseLastValue="0"/>
    <field name="rel_cn" reuseLastValue="0"/>
    <field name="residuo" reuseLastValue="0"/>
    <field name="s" reuseLastValue="0"/>
    <field name="segmento" reuseLastValue="0"/>
    <field name="suelo" reuseLastValue="0"/>
    <field name="ti" reuseLastValue="0"/>
    <field name="zn" reuseLastValue="0"/>
  </reuseLastValue>
  <dataDefinedFieldProperties/>
  <widgets/>
  <previewExpression>lote || '-' ||segmento</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
