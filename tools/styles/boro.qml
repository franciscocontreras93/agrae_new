<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyAlgorithm="0" hasScaleBasedVisibilityFlag="0" styleCategories="AllStyleCategories" symbologyReferenceScale="-1" readOnly="0" simplifyDrawingHints="1" simplifyDrawingTol="1" maxScale="0" version="3.22.13-Białowieża" labelsEnabled="1" minScale="100000000" simplifyLocal="1" simplifyMaxScale="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <temporal startExpression="" endField="" durationUnit="min" endExpression="" durationField="" mode="0" limitMode="0" fixedDuration="0" accumulate="0" enabled="0" startField="">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <renderer-v2 type="RuleRenderer" referencescale="-1" symbollevels="0" enableorderby="0" forceraster="0">
    <rules key="{2867c40f-c9bf-4fbc-8671-4bd7ad19da6f}">
      <rule filter="&quot;B&quot; >= -1000.000000 AND &quot;B&quot; &lt;= 0.000000" label="ND" symbol="0" key="{9e80b0ec-6a1f-44f8-80dc-d7bf390376d2}"/>
      <rule filter="&quot;B&quot; > 0.000000 AND &quot;B&quot; &lt;= 0.200000" label="Bajo" symbol="1" key="{1bca18b1-b443-49b2-9749-4afb68bcee2c}"/>
      <rule filter="&quot;B&quot; > 0.200000 AND &quot;B&quot; &lt;= 0.600000" label="Medio" symbol="2" key="{0c119c65-2d60-4316-8355-9660da1c83b0}"/>
      <rule filter="&quot;B&quot; > 0.600000 AND &quot;B&quot; &lt;= 1.100000" label="Alto" symbol="3" key="{8f78f8e7-ea8d-45f5-8879-a6f892a5ec32}"/>
      <rule filter="&quot;B&quot; > 1.100000 AND &quot;B&quot; &lt;= 3.000000" label="Muy alto" symbol="4" key="{028830ee-ae8d-47e4-8bab-d36e9f41c5b7}"/>
      <rule filter="&quot;B&quot; > 3.000000 AND &quot;B&quot; &lt;= 1000.000000" label="Tóxico" symbol="5" key="{69e21c69-40f4-4cd5-b59d-a4b30cf369af}"/>
    </rules>
    <symbols>
      <symbol alpha="1" type="fill" force_rhr="0" clip_to_extent="1" name="0">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" locked="0" class="SimpleFill" enabled="1">
          <Option type="Map">
            <Option value="3x:0,0,0,0,0,0" type="QString" name="border_width_map_unit_scale"/>
            <Option value="233,213,198,255" type="QString" name="color"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="0,0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0,0,0,255" type="QString" name="outline_color"/>
            <Option value="no" type="QString" name="outline_style"/>
            <Option value="3" type="QString" name="outline_width"/>
            <Option value="MM" type="QString" name="outline_width_unit"/>
            <Option value="diagonal_x" type="QString" name="style"/>
          </Option>
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="233,213,198,255" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="0,0,0,255" k="outline_color"/>
          <prop v="no" k="outline_style"/>
          <prop v="3" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diagonal_x" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="fill" force_rhr="0" clip_to_extent="1" name="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" locked="0" class="SimpleFill" enabled="1">
          <Option type="Map">
            <Option value="3x:0,0,0,0,0,0" type="QString" name="border_width_map_unit_scale"/>
            <Option value="225,57,23,255" type="QString" name="color"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="0,0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0,0,0,255" type="QString" name="outline_color"/>
            <Option value="no" type="QString" name="outline_style"/>
            <Option value="0.26" type="QString" name="outline_width"/>
            <Option value="MM" type="QString" name="outline_width_unit"/>
            <Option value="solid" type="QString" name="style"/>
          </Option>
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="225,57,23,255" k="color"/>
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
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="fill" force_rhr="0" clip_to_extent="1" name="2">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" locked="0" class="SimpleFill" enabled="1">
          <Option type="Map">
            <Option value="3x:0,0,0,0,0,0" type="QString" name="border_width_map_unit_scale"/>
            <Option value="25,215,44,255" type="QString" name="color"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="0,0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0,0,0,255" type="QString" name="outline_color"/>
            <Option value="no" type="QString" name="outline_style"/>
            <Option value="0.26" type="QString" name="outline_width"/>
            <Option value="MM" type="QString" name="outline_width_unit"/>
            <Option value="solid" type="QString" name="style"/>
          </Option>
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="25,215,44,255" k="color"/>
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
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="fill" force_rhr="0" clip_to_extent="1" name="3">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" locked="0" class="SimpleFill" enabled="1">
          <Option type="Map">
            <Option value="3x:0,0,0,0,0,0" type="QString" name="border_width_map_unit_scale"/>
            <Option value="18,184,230,255" type="QString" name="color"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="0,0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0,0,0,255" type="QString" name="outline_color"/>
            <Option value="no" type="QString" name="outline_style"/>
            <Option value="0.26" type="QString" name="outline_width"/>
            <Option value="MM" type="QString" name="outline_width_unit"/>
            <Option value="solid" type="QString" name="style"/>
          </Option>
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="18,184,230,255" k="color"/>
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
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="fill" force_rhr="0" clip_to_extent="1" name="4">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" locked="0" class="SimpleFill" enabled="1">
          <Option type="Map">
            <Option value="3x:0,0,0,0,0,0" type="QString" name="border_width_map_unit_scale"/>
            <Option value="23,27,225,255" type="QString" name="color"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="0,0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0,0,0,255" type="QString" name="outline_color"/>
            <Option value="no" type="QString" name="outline_style"/>
            <Option value="0.26" type="QString" name="outline_width"/>
            <Option value="MM" type="QString" name="outline_width_unit"/>
            <Option value="solid" type="QString" name="style"/>
          </Option>
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="23,27,225,255" k="color"/>
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
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="fill" force_rhr="0" clip_to_extent="1" name="5">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" locked="0" class="SimpleFill" enabled="1">
          <Option type="Map">
            <Option value="3x:0,0,0,0,0,0" type="QString" name="border_width_map_unit_scale"/>
            <Option value="182,0,191,255" type="QString" name="color"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="0,0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0,0,0,255" type="QString" name="outline_color"/>
            <Option value="no" type="QString" name="outline_style"/>
            <Option value="0.26" type="QString" name="outline_width"/>
            <Option value="MM" type="QString" name="outline_width_unit"/>
            <Option value="solid" type="QString" name="style"/>
          </Option>
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="182,0,191,255" k="color"/>
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
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style namedStyle="Bold" fontStrikeout="0" isExpression="1" capitalization="0" legendString="Aa" fontFamily="Arial" fieldName="round(b,2) || ' ppm'" fontSizeUnit="Point" fontWordSpacing="0" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontUnderline="0" textColor="50,50,50,255" useSubstitutions="0" blendMode="0" textOpacity="1" textOrientation="horizontal" multilineHeight="1" previewBkgrdColor="255,255,255,255" fontKerning="1" fontLetterSpacing="0" allowHtml="0" fontWeight="75" fontItalic="0" fontSize="8">
        <families/>
        <text-buffer bufferDraw="1" bufferBlendMode="0" bufferSize="1" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferColor="250,250,250,255" bufferNoFill="1" bufferSizeUnits="MM" bufferOpacity="1" bufferJoinStyle="128"/>
        <text-mask maskSize="0" maskOpacity="1" maskType="0" maskEnabled="0" maskJoinStyle="128" maskSizeMapUnitScale="3x:0,0,0,0,0,0" maskSizeUnits="MM" maskedSymbolLayers=""/>
        <background shapeSVGFile="" shapeOffsetX="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeJoinStyle="64" shapeBorderWidth="0" shapeFillColor="255,255,255,255" shapeRotationType="0" shapeBorderColor="128,128,128,255" shapeDraw="0" shapeSizeX="0" shapeRadiiY="0" shapeBlendMode="0" shapeType="0" shapeSizeType="0" shapeBorderWidthUnit="Point" shapeOpacity="1" shapeRotation="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetUnit="Point" shapeSizeY="0" shapeSizeUnit="Point" shapeRadiiUnit="Point" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetY="0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiX="0">
          <symbol alpha="1" type="marker" force_rhr="0" clip_to_extent="1" name="markerSymbol">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer pass="0" locked="0" class="SimpleMarker" enabled="1">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="square" type="QString" name="cap_style"/>
                <Option value="183,72,75,255" type="QString" name="color"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="bevel" type="QString" name="joinstyle"/>
                <Option value="circle" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="35,35,35,255" type="QString" name="outline_color"/>
                <Option value="solid" type="QString" name="outline_style"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="2" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
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
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol alpha="1" type="fill" force_rhr="0" clip_to_extent="1" name="fillSymbol">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer pass="0" locked="0" class="SimpleFill" enabled="1">
              <Option type="Map">
                <Option value="3x:0,0,0,0,0,0" type="QString" name="border_width_map_unit_scale"/>
                <Option value="255,255,255,255" type="QString" name="color"/>
                <Option value="bevel" type="QString" name="joinstyle"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="128,128,128,255" type="QString" name="outline_color"/>
                <Option value="no" type="QString" name="outline_style"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="Point" type="QString" name="outline_width_unit"/>
                <Option value="solid" type="QString" name="style"/>
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
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </background>
        <shadow shadowRadiusUnit="MM" shadowBlendMode="6" shadowOffsetUnit="MM" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowUnder="0" shadowRadius="1.5" shadowOffsetGlobal="1" shadowDraw="0" shadowScale="100" shadowOffsetDist="1" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetAngle="135" shadowRadiusAlphaOnly="0" shadowColor="0,0,0,255" shadowOpacity="0.69999999999999996"/>
        <dd_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format multilineAlign="3" decimals="3" autoWrapLength="0" reverseDirectionSymbol="0" formatNumbers="0" plussign="0" wrapChar="" leftDirectionSymbol="&lt;" placeDirectionSymbol="0" useMaxLineLengthForAutoWrap="1" addDirectionSymbol="0" rightDirectionSymbol=">"/>
      <placement centroidWhole="0" distUnits="MM" lineAnchorType="0" placementFlags="10" preserveRotation="1" maxCurvedCharAngleOut="-25" yOffset="0" lineAnchorPercent="0.5" geometryGenerator="" repeatDistance="0" offsetUnits="MM" rotationUnit="AngleDegrees" fitInPolygonOnly="0" repeatDistanceUnits="MM" overrunDistance="0" maxCurvedCharAngleIn="25" offsetType="0" dist="0" centroidInside="1" rotationAngle="0" placement="0" xOffset="0" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" priority="5" layerType="PolygonGeometry" geometryGeneratorEnabled="0" polygonPlacementFlags="2" geometryGeneratorType="PointGeometry" quadOffset="4" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" lineAnchorClipping="0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" distMapUnitScale="3x:0,0,0,0,0,0" overrunDistanceUnit="MM"/>
      <rendering zIndex="0" labelPerPart="0" obstacle="1" minFeatureSize="0" scaleVisibility="0" scaleMax="0" fontMinPixelSize="3" drawLabels="1" fontMaxPixelSize="10000" upsidedownLabels="0" mergeLines="0" limitNumLabels="0" displayAll="0" unplacedVisibility="0" obstacleType="1" maxNumLabels="2000" obstacleFactor="1" scaleMin="0" fontLimitPixelSize="0"/>
      <dd_properties>
        <Option type="Map">
          <Option value="" type="QString" name="name"/>
          <Option name="properties"/>
          <Option value="collection" type="QString" name="type"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option value="pole_of_inaccessibility" type="QString" name="anchorPoint"/>
          <Option value="0" type="int" name="blendMode"/>
          <Option type="Map" name="ddProperties">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
          <Option value="false" type="bool" name="drawToAllParts"/>
          <Option value="0" type="QString" name="enabled"/>
          <Option value="point_on_exterior" type="QString" name="labelAnchorPoint"/>
          <Option value="&lt;symbol alpha=&quot;1&quot; type=&quot;line&quot; force_rhr=&quot;0&quot; clip_to_extent=&quot;1&quot; name=&quot;symbol&quot;>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option value=&quot;&quot; type=&quot;QString&quot; name=&quot;name&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option value=&quot;collection&quot; type=&quot;QString&quot; name=&quot;type&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;layer pass=&quot;0&quot; locked=&quot;0&quot; class=&quot;SimpleLine&quot; enabled=&quot;1&quot;>&lt;Option type=&quot;Map&quot;>&lt;Option value=&quot;0&quot; type=&quot;QString&quot; name=&quot;align_dash_pattern&quot;/>&lt;Option value=&quot;square&quot; type=&quot;QString&quot; name=&quot;capstyle&quot;/>&lt;Option value=&quot;5;2&quot; type=&quot;QString&quot; name=&quot;customdash&quot;/>&lt;Option value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot; name=&quot;customdash_map_unit_scale&quot;/>&lt;Option value=&quot;MM&quot; type=&quot;QString&quot; name=&quot;customdash_unit&quot;/>&lt;Option value=&quot;0&quot; type=&quot;QString&quot; name=&quot;dash_pattern_offset&quot;/>&lt;Option value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot; name=&quot;dash_pattern_offset_map_unit_scale&quot;/>&lt;Option value=&quot;MM&quot; type=&quot;QString&quot; name=&quot;dash_pattern_offset_unit&quot;/>&lt;Option value=&quot;0&quot; type=&quot;QString&quot; name=&quot;draw_inside_polygon&quot;/>&lt;Option value=&quot;bevel&quot; type=&quot;QString&quot; name=&quot;joinstyle&quot;/>&lt;Option value=&quot;60,60,60,255&quot; type=&quot;QString&quot; name=&quot;line_color&quot;/>&lt;Option value=&quot;solid&quot; type=&quot;QString&quot; name=&quot;line_style&quot;/>&lt;Option value=&quot;0.3&quot; type=&quot;QString&quot; name=&quot;line_width&quot;/>&lt;Option value=&quot;MM&quot; type=&quot;QString&quot; name=&quot;line_width_unit&quot;/>&lt;Option value=&quot;0&quot; type=&quot;QString&quot; name=&quot;offset&quot;/>&lt;Option value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot; name=&quot;offset_map_unit_scale&quot;/>&lt;Option value=&quot;MM&quot; type=&quot;QString&quot; name=&quot;offset_unit&quot;/>&lt;Option value=&quot;0&quot; type=&quot;QString&quot; name=&quot;ring_filter&quot;/>&lt;Option value=&quot;0&quot; type=&quot;QString&quot; name=&quot;trim_distance_end&quot;/>&lt;Option value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot; name=&quot;trim_distance_end_map_unit_scale&quot;/>&lt;Option value=&quot;MM&quot; type=&quot;QString&quot; name=&quot;trim_distance_end_unit&quot;/>&lt;Option value=&quot;0&quot; type=&quot;QString&quot; name=&quot;trim_distance_start&quot;/>&lt;Option value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot; name=&quot;trim_distance_start_map_unit_scale&quot;/>&lt;Option value=&quot;MM&quot; type=&quot;QString&quot; name=&quot;trim_distance_start_unit&quot;/>&lt;Option value=&quot;0&quot; type=&quot;QString&quot; name=&quot;tweak_dash_pattern_on_corners&quot;/>&lt;Option value=&quot;0&quot; type=&quot;QString&quot; name=&quot;use_custom_dash&quot;/>&lt;Option value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot; name=&quot;width_map_unit_scale&quot;/>&lt;/Option>&lt;prop v=&quot;0&quot; k=&quot;align_dash_pattern&quot;/>&lt;prop v=&quot;square&quot; k=&quot;capstyle&quot;/>&lt;prop v=&quot;5;2&quot; k=&quot;customdash&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;customdash_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;customdash_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;dash_pattern_offset&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;dash_pattern_offset_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;dash_pattern_offset_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;draw_inside_polygon&quot;/>&lt;prop v=&quot;bevel&quot; k=&quot;joinstyle&quot;/>&lt;prop v=&quot;60,60,60,255&quot; k=&quot;line_color&quot;/>&lt;prop v=&quot;solid&quot; k=&quot;line_style&quot;/>&lt;prop v=&quot;0.3&quot; k=&quot;line_width&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;line_width_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;offset&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;offset_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;offset_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;ring_filter&quot;/>&lt;prop v=&quot;0&quot; k=&quot;trim_distance_end&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;trim_distance_end_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;trim_distance_end_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;trim_distance_start&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;trim_distance_start_map_unit_scale&quot;/>&lt;prop v=&quot;MM&quot; k=&quot;trim_distance_start_unit&quot;/>&lt;prop v=&quot;0&quot; k=&quot;tweak_dash_pattern_on_corners&quot;/>&lt;prop v=&quot;0&quot; k=&quot;use_custom_dash&quot;/>&lt;prop v=&quot;3x:0,0,0,0,0,0&quot; k=&quot;width_map_unit_scale&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option value=&quot;&quot; type=&quot;QString&quot; name=&quot;name&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option value=&quot;collection&quot; type=&quot;QString&quot; name=&quot;type&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>" type="QString" name="lineSymbol"/>
          <Option value="0" type="double" name="minLength"/>
          <Option value="3x:0,0,0,0,0,0" type="QString" name="minLengthMapUnitScale"/>
          <Option value="MM" type="QString" name="minLengthUnit"/>
          <Option value="0" type="double" name="offsetFromAnchor"/>
          <Option value="3x:0,0,0,0,0,0" type="QString" name="offsetFromAnchorMapUnitScale"/>
          <Option value="MM" type="QString" name="offsetFromAnchorUnit"/>
          <Option value="0" type="double" name="offsetFromLabel"/>
          <Option value="3x:0,0,0,0,0,0" type="QString" name="offsetFromLabelMapUnitScale"/>
          <Option value="MM" type="QString" name="offsetFromLabelUnit"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <customproperties>
    <Option type="Map">
      <Option value="offline" type="QString" name="QFieldSync/action"/>
      <Option value="offline" type="QString" name="QFieldSync/cloud_action"/>
      <Option value="{}" type="QString" name="QFieldSync/photo_naming"/>
      <Option type="List" name="dualview/previewExpressions">
        <Option value="lote || '-' ||segmento" type="QString"/>
      </Option>
      <Option value="0" type="QString" name="embeddedWidgets/count"/>
      <Option value="&quot;idlotecampania&quot; in (366, 371, 361, 368, 370, 363, 362, 369, 367)" type="QString" name="subset_expression"/>
      <Option value="0" type="int" name="subset_expression_checked"/>
      <Option name="variableNames"/>
      <Option name="variableValues"/>
    </Option>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>0.7</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory lineSizeScale="3x:0,0,0,0,0,0" penColor="#000000" sizeType="MM" spacingUnit="MM" lineSizeType="MM" backgroundColor="#ffffff" scaleDependency="Area" height="15" width="15" spacing="0" rotationOffset="270" penWidth="0" direction="1" sizeScale="3x:0,0,0,0,0,0" enabled="0" scaleBasedVisibility="0" minScaleDenominator="0" diagramOrientation="Up" maxScaleDenominator="1e+08" opacity="1" backgroundAlpha="255" minimumSize="0" barWidth="5" labelPlacementMethod="XHeight" penAlpha="255" spacingUnitScale="3x:0,0,0,0,0,0" showAxis="0">
      <fontProperties description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0" style=""/>
      <attribute label="" field="" color="#000000" colorOpacity="1"/>
      <axisSymbol>
        <symbol alpha="1" type="line" force_rhr="0" clip_to_extent="1" name="">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <layer pass="0" locked="0" class="SimpleLine" enabled="1">
            <Option type="Map">
              <Option value="0" type="QString" name="align_dash_pattern"/>
              <Option value="square" type="QString" name="capstyle"/>
              <Option value="5;2" type="QString" name="customdash"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
              <Option value="MM" type="QString" name="customdash_unit"/>
              <Option value="0" type="QString" name="dash_pattern_offset"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
              <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
              <Option value="0" type="QString" name="draw_inside_polygon"/>
              <Option value="bevel" type="QString" name="joinstyle"/>
              <Option value="35,35,35,255" type="QString" name="line_color"/>
              <Option value="solid" type="QString" name="line_style"/>
              <Option value="0.26" type="QString" name="line_width"/>
              <Option value="MM" type="QString" name="line_width_unit"/>
              <Option value="0" type="QString" name="offset"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
              <Option value="MM" type="QString" name="offset_unit"/>
              <Option value="0" type="QString" name="ring_filter"/>
              <Option value="0" type="QString" name="trim_distance_end"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
              <Option value="MM" type="QString" name="trim_distance_end_unit"/>
              <Option value="0" type="QString" name="trim_distance_start"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
              <Option value="MM" type="QString" name="trim_distance_start_unit"/>
              <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
              <Option value="0" type="QString" name="use_custom_dash"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
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
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
      </axisSymbol>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings zIndex="0" obstacle="0" showAll="1" placement="1" linePlacementFlags="18" priority="0" dist="0">
    <properties>
      <Option type="Map">
        <Option value="" type="QString" name="name"/>
        <Option name="properties"/>
        <Option value="collection" type="QString" name="type"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
    <activeChecks/>
    <checkConfiguration type="Map">
      <Option type="Map" name="QgsGeometryGapCheck">
        <Option value="0" type="double" name="allowedGapsBuffer"/>
        <Option value="false" type="bool" name="allowedGapsEnabled"/>
        <Option value="" type="QString" name="allowedGapsLayer"/>
      </Option>
    </checkConfiguration>
  </geometryOptions>
  <legend type="default-vector" showLabelLegend="0"/>
  <referencedLayers/>
  <fieldConfiguration>
    <field configurationFlags="None" name="id">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="lote">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="b">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="cod_muestra">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias index="0" field="id" name=""/>
    <alias index="1" field="lote" name=""/>
    <alias index="2" field="b" name=""/>
    <alias index="3" field="cod_muestra" name=""/>
  </aliases>
  <defaults>
    <default applyOnUpdate="0" field="id" expression=""/>
    <default applyOnUpdate="0" field="lote" expression=""/>
    <default applyOnUpdate="0" field="b" expression=""/>
    <default applyOnUpdate="0" field="cod_muestra" expression=""/>
  </defaults>
  <constraints>
    <constraint unique_strength="1" field="id" notnull_strength="1" constraints="3" exp_strength="0"/>
    <constraint unique_strength="0" field="lote" notnull_strength="0" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" field="b" notnull_strength="0" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" field="cod_muestra" notnull_strength="0" constraints="0" exp_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" field="id" exp=""/>
    <constraint desc="" field="lote" exp=""/>
    <constraint desc="" field="b" exp=""/>
    <constraint desc="" field="cod_muestra" exp=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" actionWidgetStyle="dropDown" sortExpression="&quot;b&quot;">
    <columns>
      <column hidden="1" type="actions" width="-1"/>
      <column hidden="0" type="field" width="-1" name="b"/>
      <column hidden="0" type="field" width="-1" name="lote"/>
      <column hidden="0" type="field" width="-1" name="cod_muestra"/>
      <column hidden="0" type="field" width="100" name="id"/>
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
    <field editable="1" name="AL"/>
    <field editable="1" name="AREA"/>
    <field editable="1" name="ATLAS"/>
    <field editable="1" name="ATLAS_2"/>
    <field editable="1" name="B"/>
    <field editable="1" name="BIOMASA"/>
    <field editable="1" name="CA"/>
    <field editable="1" name="CALIZA"/>
    <field editable="1" name="CARBON"/>
    <field editable="1" name="CARB_LABEL"/>
    <field editable="1" name="CARB_NIVEL"/>
    <field editable="1" name="CAR_NIVELT"/>
    <field editable="1" name="CA_EQ"/>
    <field editable="1" name="CA_F"/>
    <field editable="1" name="CE"/>
    <field editable="1" name="CE_LABEL"/>
    <field editable="1" name="CE_NIVEL"/>
    <field editable="1" name="CE_NIVELTE"/>
    <field editable="1" name="CEap"/>
    <field editable="1" name="CIC"/>
    <field editable="1" name="COB01"/>
    <field editable="1" name="COB02"/>
    <field editable="1" name="COD"/>
    <field editable="1" name="CODTEXT"/>
    <field editable="1" name="COSECHA"/>
    <field editable="1" name="COX"/>
    <field editable="1" name="CU"/>
    <field editable="1" name="CULTIVO_0"/>
    <field editable="1" name="CULTIVO_1"/>
    <field editable="1" name="EST_RESIDU"/>
    <field editable="1" name="FE"/>
    <field editable="1" name="FIRST_ATLA"/>
    <field editable="1" name="FONDO"/>
    <field editable="1" name="F_COB01"/>
    <field editable="1" name="F_COB02"/>
    <field editable="1" name="F_FONDO"/>
    <field editable="1" name="GUIA"/>
    <field editable="1" name="INDREPR"/>
    <field editable="1" name="K"/>
    <field editable="1" name="K_APORT"/>
    <field editable="1" name="K_ECOSECH"/>
    <field editable="1" name="K_EQ"/>
    <field editable="1" name="K_ERESI"/>
    <field editable="1" name="K_F"/>
    <field editable="1" name="K_INC"/>
    <field editable="1" name="K_LABEL"/>
    <field editable="1" name="K_NECESID"/>
    <field editable="1" name="K_NIVEL"/>
    <field editable="1" name="K_NIVELTEX"/>
    <field editable="1" name="Kf"/>
    <field editable="1" name="MG"/>
    <field editable="1" name="MG_EQ"/>
    <field editable="1" name="MG_F"/>
    <field editable="1" name="MN"/>
    <field editable="1" name="MO"/>
    <field editable="1" name="N"/>
    <field editable="1" name="NA"/>
    <field editable="1" name="NAME_PARC"/>
    <field editable="1" name="NA_EQ"/>
    <field editable="1" name="NA_F"/>
    <field editable="1" name="NN"/>
    <field editable="1" name="NOMBRE_AGR"/>
    <field editable="1" name="N_APORT"/>
    <field editable="1" name="N_ECOSECH"/>
    <field editable="1" name="N_ERESI"/>
    <field editable="1" name="N_INC"/>
    <field editable="1" name="N_LABEL"/>
    <field editable="1" name="N_NECESID"/>
    <field editable="1" name="N_NIVEL"/>
    <field editable="1" name="N_NIVELTEX"/>
    <field editable="1" name="OBJ"/>
    <field editable="1" name="OBJECTID"/>
    <field editable="1" name="OBJ_SEGM"/>
    <field editable="1" name="ORGANICA"/>
    <field editable="1" name="ORIG_FID"/>
    <field editable="1" name="P"/>
    <field editable="1" name="PH"/>
    <field editable="1" name="PH_LABEL"/>
    <field editable="1" name="PH_NIVEL"/>
    <field editable="1" name="PH_NIVELTE"/>
    <field editable="1" name="P_APORT"/>
    <field editable="1" name="P_ECOSECH"/>
    <field editable="1" name="P_ERESI"/>
    <field editable="1" name="P_INC"/>
    <field editable="1" name="P_LABEL"/>
    <field editable="1" name="P_NECESID"/>
    <field editable="1" name="P_NIVEL"/>
    <field editable="1" name="P_NIVELTEX"/>
    <field editable="1" name="REF_SERIE"/>
    <field editable="1" name="REL_CN"/>
    <field editable="1" name="RESIDUO"/>
    <field editable="1" name="S"/>
    <field editable="1" name="SEGM"/>
    <field editable="1" name="SERIE"/>
    <field editable="1" name="Shape_Area"/>
    <field editable="1" name="Shape_Leng"/>
    <field editable="1" name="TEXTURA"/>
    <field editable="1" name="ZN"/>
    <field editable="1" name="al"/>
    <field editable="1" name="arcilla"/>
    <field editable="1" name="arena"/>
    <field editable="1" name="as"/>
    <field editable="1" name="b"/>
    <field editable="1" name="biomasa"/>
    <field editable="1" name="ca"/>
    <field editable="1" name="ca_eq"/>
    <field editable="1" name="ca_f"/>
    <field editable="1" name="ca_inc"/>
    <field editable="1" name="ca_tipo"/>
    <field editable="1" name="caliza"/>
    <field editable="1" name="caliza_tipo"/>
    <field editable="1" name="carb_tipo"/>
    <field editable="1" name="carbonatos"/>
    <field editable="1" name="ce"/>
    <field editable="1" name="ce_influencia"/>
    <field editable="1" name="ce_tipo"/>
    <field editable="1" name="ceap"/>
    <field editable="1" name="cic"/>
    <field editable="1" name="cic_caso"/>
    <field editable="1" name="cic_tipo"/>
    <field editable="1" name="co"/>
    <field editable="1" name="cod_control"/>
    <field editable="1" name="cod_muestra"/>
    <field editable="1" name="cox"/>
    <field editable="1" name="cr"/>
    <field editable="1" name="cu"/>
    <field editable="1" name="cultivo"/>
    <field editable="1" name="exp_nombre"/>
    <field editable="1" name="fe"/>
    <field editable="1" name="fechasiembra"/>
    <field editable="1" name="g_suelo"/>
    <field editable="1" name="id"/>
    <field editable="1" name="idanalitica"/>
    <field editable="1" name="idexp"/>
    <field editable="1" name="idlotecampania"/>
    <field editable="1" name="idsegmento"/>
    <field editable="1" name="idsegmentoanalisis"/>
    <field editable="1" name="k"/>
    <field editable="1" name="k_eq"/>
    <field editable="1" name="k_f"/>
    <field editable="1" name="k_inc"/>
    <field editable="1" name="k_tipo"/>
    <field editable="1" name="layer"/>
    <field editable="1" name="limo"/>
    <field editable="1" name="lote"/>
    <field editable="1" name="mg"/>
    <field editable="1" name="mg_eq"/>
    <field editable="1" name="mg_f"/>
    <field editable="1" name="mg_inc"/>
    <field editable="1" name="mg_tipo"/>
    <field editable="1" name="mn"/>
    <field editable="1" name="mo"/>
    <field editable="1" name="n"/>
    <field editable="1" name="n_inc"/>
    <field editable="1" name="n_tipo"/>
    <field editable="1" name="na"/>
    <field editable="1" name="na_eq"/>
    <field editable="1" name="na_f"/>
    <field editable="1" name="na_inc"/>
    <field editable="1" name="na_tipo"/>
    <field editable="1" name="ni"/>
    <field editable="1" name="organi"/>
    <field editable="1" name="p"/>
    <field editable="1" name="p_inc"/>
    <field editable="1" name="p_metodo"/>
    <field editable="1" name="p_tipo"/>
    <field editable="1" name="path"/>
    <field editable="1" name="pb"/>
    <field editable="1" name="ph"/>
    <field editable="1" name="ph_tipo"/>
    <field editable="1" name="pk_uid"/>
    <field editable="1" name="prod_esperada"/>
    <field editable="1" name="regimen"/>
    <field editable="1" name="rel_cn"/>
    <field editable="1" name="residuo"/>
    <field editable="1" name="s"/>
    <field editable="1" name="segmento"/>
    <field editable="1" name="suelo"/>
    <field editable="1" name="ti"/>
    <field editable="1" name="zn"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="AL"/>
    <field labelOnTop="0" name="AREA"/>
    <field labelOnTop="0" name="ATLAS"/>
    <field labelOnTop="0" name="ATLAS_2"/>
    <field labelOnTop="0" name="B"/>
    <field labelOnTop="0" name="BIOMASA"/>
    <field labelOnTop="0" name="CA"/>
    <field labelOnTop="0" name="CALIZA"/>
    <field labelOnTop="0" name="CARBON"/>
    <field labelOnTop="0" name="CARB_LABEL"/>
    <field labelOnTop="0" name="CARB_NIVEL"/>
    <field labelOnTop="0" name="CAR_NIVELT"/>
    <field labelOnTop="0" name="CA_EQ"/>
    <field labelOnTop="0" name="CA_F"/>
    <field labelOnTop="0" name="CE"/>
    <field labelOnTop="0" name="CE_LABEL"/>
    <field labelOnTop="0" name="CE_NIVEL"/>
    <field labelOnTop="0" name="CE_NIVELTE"/>
    <field labelOnTop="0" name="CEap"/>
    <field labelOnTop="0" name="CIC"/>
    <field labelOnTop="0" name="COB01"/>
    <field labelOnTop="0" name="COB02"/>
    <field labelOnTop="0" name="COD"/>
    <field labelOnTop="0" name="CODTEXT"/>
    <field labelOnTop="0" name="COSECHA"/>
    <field labelOnTop="0" name="COX"/>
    <field labelOnTop="0" name="CU"/>
    <field labelOnTop="0" name="CULTIVO_0"/>
    <field labelOnTop="0" name="CULTIVO_1"/>
    <field labelOnTop="0" name="EST_RESIDU"/>
    <field labelOnTop="0" name="FE"/>
    <field labelOnTop="0" name="FIRST_ATLA"/>
    <field labelOnTop="0" name="FONDO"/>
    <field labelOnTop="0" name="F_COB01"/>
    <field labelOnTop="0" name="F_COB02"/>
    <field labelOnTop="0" name="F_FONDO"/>
    <field labelOnTop="0" name="GUIA"/>
    <field labelOnTop="0" name="INDREPR"/>
    <field labelOnTop="0" name="K"/>
    <field labelOnTop="0" name="K_APORT"/>
    <field labelOnTop="0" name="K_ECOSECH"/>
    <field labelOnTop="0" name="K_EQ"/>
    <field labelOnTop="0" name="K_ERESI"/>
    <field labelOnTop="0" name="K_F"/>
    <field labelOnTop="0" name="K_INC"/>
    <field labelOnTop="0" name="K_LABEL"/>
    <field labelOnTop="0" name="K_NECESID"/>
    <field labelOnTop="0" name="K_NIVEL"/>
    <field labelOnTop="0" name="K_NIVELTEX"/>
    <field labelOnTop="0" name="Kf"/>
    <field labelOnTop="0" name="MG"/>
    <field labelOnTop="0" name="MG_EQ"/>
    <field labelOnTop="0" name="MG_F"/>
    <field labelOnTop="0" name="MN"/>
    <field labelOnTop="0" name="MO"/>
    <field labelOnTop="0" name="N"/>
    <field labelOnTop="0" name="NA"/>
    <field labelOnTop="0" name="NAME_PARC"/>
    <field labelOnTop="0" name="NA_EQ"/>
    <field labelOnTop="0" name="NA_F"/>
    <field labelOnTop="0" name="NN"/>
    <field labelOnTop="0" name="NOMBRE_AGR"/>
    <field labelOnTop="0" name="N_APORT"/>
    <field labelOnTop="0" name="N_ECOSECH"/>
    <field labelOnTop="0" name="N_ERESI"/>
    <field labelOnTop="0" name="N_INC"/>
    <field labelOnTop="0" name="N_LABEL"/>
    <field labelOnTop="0" name="N_NECESID"/>
    <field labelOnTop="0" name="N_NIVEL"/>
    <field labelOnTop="0" name="N_NIVELTEX"/>
    <field labelOnTop="0" name="OBJ"/>
    <field labelOnTop="0" name="OBJECTID"/>
    <field labelOnTop="0" name="OBJ_SEGM"/>
    <field labelOnTop="0" name="ORGANICA"/>
    <field labelOnTop="0" name="ORIG_FID"/>
    <field labelOnTop="0" name="P"/>
    <field labelOnTop="0" name="PH"/>
    <field labelOnTop="0" name="PH_LABEL"/>
    <field labelOnTop="0" name="PH_NIVEL"/>
    <field labelOnTop="0" name="PH_NIVELTE"/>
    <field labelOnTop="0" name="P_APORT"/>
    <field labelOnTop="0" name="P_ECOSECH"/>
    <field labelOnTop="0" name="P_ERESI"/>
    <field labelOnTop="0" name="P_INC"/>
    <field labelOnTop="0" name="P_LABEL"/>
    <field labelOnTop="0" name="P_NECESID"/>
    <field labelOnTop="0" name="P_NIVEL"/>
    <field labelOnTop="0" name="P_NIVELTEX"/>
    <field labelOnTop="0" name="REF_SERIE"/>
    <field labelOnTop="0" name="REL_CN"/>
    <field labelOnTop="0" name="RESIDUO"/>
    <field labelOnTop="0" name="S"/>
    <field labelOnTop="0" name="SEGM"/>
    <field labelOnTop="0" name="SERIE"/>
    <field labelOnTop="0" name="Shape_Area"/>
    <field labelOnTop="0" name="Shape_Leng"/>
    <field labelOnTop="0" name="TEXTURA"/>
    <field labelOnTop="0" name="ZN"/>
    <field labelOnTop="0" name="al"/>
    <field labelOnTop="0" name="arcilla"/>
    <field labelOnTop="0" name="arena"/>
    <field labelOnTop="0" name="as"/>
    <field labelOnTop="0" name="b"/>
    <field labelOnTop="0" name="biomasa"/>
    <field labelOnTop="0" name="ca"/>
    <field labelOnTop="0" name="ca_eq"/>
    <field labelOnTop="0" name="ca_f"/>
    <field labelOnTop="0" name="ca_inc"/>
    <field labelOnTop="0" name="ca_tipo"/>
    <field labelOnTop="0" name="caliza"/>
    <field labelOnTop="0" name="caliza_tipo"/>
    <field labelOnTop="0" name="carb_tipo"/>
    <field labelOnTop="0" name="carbonatos"/>
    <field labelOnTop="0" name="ce"/>
    <field labelOnTop="0" name="ce_influencia"/>
    <field labelOnTop="0" name="ce_tipo"/>
    <field labelOnTop="0" name="ceap"/>
    <field labelOnTop="0" name="cic"/>
    <field labelOnTop="0" name="cic_caso"/>
    <field labelOnTop="0" name="cic_tipo"/>
    <field labelOnTop="0" name="co"/>
    <field labelOnTop="0" name="cod_control"/>
    <field labelOnTop="0" name="cod_muestra"/>
    <field labelOnTop="0" name="cox"/>
    <field labelOnTop="0" name="cr"/>
    <field labelOnTop="0" name="cu"/>
    <field labelOnTop="0" name="cultivo"/>
    <field labelOnTop="0" name="exp_nombre"/>
    <field labelOnTop="0" name="fe"/>
    <field labelOnTop="0" name="fechasiembra"/>
    <field labelOnTop="0" name="g_suelo"/>
    <field labelOnTop="0" name="id"/>
    <field labelOnTop="0" name="idanalitica"/>
    <field labelOnTop="0" name="idexp"/>
    <field labelOnTop="0" name="idlotecampania"/>
    <field labelOnTop="0" name="idsegmento"/>
    <field labelOnTop="0" name="idsegmentoanalisis"/>
    <field labelOnTop="0" name="k"/>
    <field labelOnTop="0" name="k_eq"/>
    <field labelOnTop="0" name="k_f"/>
    <field labelOnTop="0" name="k_inc"/>
    <field labelOnTop="0" name="k_tipo"/>
    <field labelOnTop="0" name="layer"/>
    <field labelOnTop="0" name="limo"/>
    <field labelOnTop="0" name="lote"/>
    <field labelOnTop="0" name="mg"/>
    <field labelOnTop="0" name="mg_eq"/>
    <field labelOnTop="0" name="mg_f"/>
    <field labelOnTop="0" name="mg_inc"/>
    <field labelOnTop="0" name="mg_tipo"/>
    <field labelOnTop="0" name="mn"/>
    <field labelOnTop="0" name="mo"/>
    <field labelOnTop="0" name="n"/>
    <field labelOnTop="0" name="n_inc"/>
    <field labelOnTop="0" name="n_tipo"/>
    <field labelOnTop="0" name="na"/>
    <field labelOnTop="0" name="na_eq"/>
    <field labelOnTop="0" name="na_f"/>
    <field labelOnTop="0" name="na_inc"/>
    <field labelOnTop="0" name="na_tipo"/>
    <field labelOnTop="0" name="ni"/>
    <field labelOnTop="0" name="organi"/>
    <field labelOnTop="0" name="p"/>
    <field labelOnTop="0" name="p_inc"/>
    <field labelOnTop="0" name="p_metodo"/>
    <field labelOnTop="0" name="p_tipo"/>
    <field labelOnTop="0" name="path"/>
    <field labelOnTop="0" name="pb"/>
    <field labelOnTop="0" name="ph"/>
    <field labelOnTop="0" name="ph_tipo"/>
    <field labelOnTop="0" name="pk_uid"/>
    <field labelOnTop="0" name="prod_esperada"/>
    <field labelOnTop="0" name="regimen"/>
    <field labelOnTop="0" name="rel_cn"/>
    <field labelOnTop="0" name="residuo"/>
    <field labelOnTop="0" name="s"/>
    <field labelOnTop="0" name="segmento"/>
    <field labelOnTop="0" name="suelo"/>
    <field labelOnTop="0" name="ti"/>
    <field labelOnTop="0" name="zn"/>
  </labelOnTop>
  <reuseLastValue>
    <field reuseLastValue="0" name="al"/>
    <field reuseLastValue="0" name="arcilla"/>
    <field reuseLastValue="0" name="arena"/>
    <field reuseLastValue="0" name="as"/>
    <field reuseLastValue="0" name="b"/>
    <field reuseLastValue="0" name="biomasa"/>
    <field reuseLastValue="0" name="ca"/>
    <field reuseLastValue="0" name="ca_eq"/>
    <field reuseLastValue="0" name="ca_f"/>
    <field reuseLastValue="0" name="ca_inc"/>
    <field reuseLastValue="0" name="ca_tipo"/>
    <field reuseLastValue="0" name="caliza"/>
    <field reuseLastValue="0" name="caliza_tipo"/>
    <field reuseLastValue="0" name="carb_tipo"/>
    <field reuseLastValue="0" name="carbonatos"/>
    <field reuseLastValue="0" name="ce"/>
    <field reuseLastValue="0" name="ce_influencia"/>
    <field reuseLastValue="0" name="ce_tipo"/>
    <field reuseLastValue="0" name="ceap"/>
    <field reuseLastValue="0" name="cic"/>
    <field reuseLastValue="0" name="cic_caso"/>
    <field reuseLastValue="0" name="cic_tipo"/>
    <field reuseLastValue="0" name="co"/>
    <field reuseLastValue="0" name="cod_control"/>
    <field reuseLastValue="0" name="cod_muestra"/>
    <field reuseLastValue="0" name="cox"/>
    <field reuseLastValue="0" name="cr"/>
    <field reuseLastValue="0" name="cu"/>
    <field reuseLastValue="0" name="cultivo"/>
    <field reuseLastValue="0" name="exp_nombre"/>
    <field reuseLastValue="0" name="fe"/>
    <field reuseLastValue="0" name="fechasiembra"/>
    <field reuseLastValue="0" name="g_suelo"/>
    <field reuseLastValue="0" name="id"/>
    <field reuseLastValue="0" name="idanalitica"/>
    <field reuseLastValue="0" name="idexp"/>
    <field reuseLastValue="0" name="idlotecampania"/>
    <field reuseLastValue="0" name="idsegmento"/>
    <field reuseLastValue="0" name="idsegmentoanalisis"/>
    <field reuseLastValue="0" name="k"/>
    <field reuseLastValue="0" name="k_eq"/>
    <field reuseLastValue="0" name="k_f"/>
    <field reuseLastValue="0" name="k_inc"/>
    <field reuseLastValue="0" name="k_tipo"/>
    <field reuseLastValue="0" name="limo"/>
    <field reuseLastValue="0" name="lote"/>
    <field reuseLastValue="0" name="mg"/>
    <field reuseLastValue="0" name="mg_eq"/>
    <field reuseLastValue="0" name="mg_f"/>
    <field reuseLastValue="0" name="mg_inc"/>
    <field reuseLastValue="0" name="mg_tipo"/>
    <field reuseLastValue="0" name="mn"/>
    <field reuseLastValue="0" name="mo"/>
    <field reuseLastValue="0" name="n"/>
    <field reuseLastValue="0" name="n_inc"/>
    <field reuseLastValue="0" name="n_tipo"/>
    <field reuseLastValue="0" name="na"/>
    <field reuseLastValue="0" name="na_eq"/>
    <field reuseLastValue="0" name="na_f"/>
    <field reuseLastValue="0" name="na_inc"/>
    <field reuseLastValue="0" name="na_tipo"/>
    <field reuseLastValue="0" name="ni"/>
    <field reuseLastValue="0" name="organi"/>
    <field reuseLastValue="0" name="p"/>
    <field reuseLastValue="0" name="p_inc"/>
    <field reuseLastValue="0" name="p_metodo"/>
    <field reuseLastValue="0" name="p_tipo"/>
    <field reuseLastValue="0" name="pb"/>
    <field reuseLastValue="0" name="ph"/>
    <field reuseLastValue="0" name="ph_tipo"/>
    <field reuseLastValue="0" name="prod_esperada"/>
    <field reuseLastValue="0" name="regimen"/>
    <field reuseLastValue="0" name="rel_cn"/>
    <field reuseLastValue="0" name="residuo"/>
    <field reuseLastValue="0" name="s"/>
    <field reuseLastValue="0" name="segmento"/>
    <field reuseLastValue="0" name="suelo"/>
    <field reuseLastValue="0" name="ti"/>
    <field reuseLastValue="0" name="zn"/>
  </reuseLastValue>
  <dataDefinedFieldProperties/>
  <widgets/>
  <previewExpression>lote || '-' ||segmento</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
