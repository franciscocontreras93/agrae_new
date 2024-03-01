<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.22.13-Białowieża" simplifyMaxScale="1" simplifyDrawingHints="1" styleCategories="AllStyleCategories" minScale="100000000" labelsEnabled="1" simplifyDrawingTol="1" simplifyLocal="1" symbologyReferenceScale="-1" hasScaleBasedVisibilityFlag="0" maxScale="0" readOnly="0" simplifyAlgorithm="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <temporal endExpression="" durationUnit="min" startField="" endField="" limitMode="0" startExpression="" mode="0" accumulate="0" fixedDuration="0" durationField="" enabled="0">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <renderer-v2 symbollevels="0" type="RuleRenderer" forceraster="0" enableorderby="0" referencescale="-1">
    <rules key="{2867c40f-c9bf-4fbc-8671-4bd7ad19da6f}">
      <rule symbol="0" filter="&quot;FE&quot; >= -100000.000000 AND &quot;FE&quot; &lt;= 0.000000 OR &quot;FE&quot; IS NULL" label="ND" key="{ef163332-ba60-4a20-a2f3-55fabcb6d46e}"/>
      <rule symbol="1" filter="&quot;FE&quot; > 0.000000 AND &quot;FE&quot; &lt;= 0.500000" label=" 0 - 0.5 ppm" key="{cae15c78-49e5-40b2-ae91-5557bb88f78a}"/>
      <rule symbol="2" filter="&quot;FE&quot; > 0.500000 AND &quot;FE&quot; &lt;= 1.000000" label=" 0.5 - 1 ppm" key="{2e72b99e-d356-46f2-b443-a7ca2e1f420a}"/>
      <rule symbol="3" filter="&quot;FE&quot; > 1.000000 AND &quot;FE&quot; &lt;= 2.000000" label=" 1 - 2 ppm" key="{bcd0e079-4f6f-4902-b444-934c3e8fd80a}"/>
      <rule symbol="4" filter="&quot;FE&quot; > 2.000000 AND &quot;FE&quot; &lt;= 4.000000" label=" 2 - 4 ppm" key="{7d12bcb5-d10b-43c1-a14c-79c6a192f326}"/>
      <rule symbol="5" filter="&quot;FE&quot; > 4.000000 AND &quot;FE&quot; &lt;= 8.000000" label=" 4 - 8 ppm" key="{b3d5a0af-edfa-441e-9d0e-aa2b5cc17d29}"/>
      <rule symbol="6" filter="&quot;FE&quot; > 8.000000 AND &quot;FE&quot; &lt;= 16.000000" label=" 8 - 16 ppm" key="{639435f2-c396-4fee-a967-e4e623872e8a}"/>
      <rule symbol="7" filter="&quot;FE&quot; > 16.000000 AND &quot;FE&quot; &lt;= 32.000000" label=" 16 - 32 ppm" key="{61ac5a97-a376-4fde-b9e5-e85b4f5f2070}"/>
      <rule symbol="8" filter="&quot;FE&quot; > 32.000000 AND &quot;FE&quot; &lt;= 64.000000" label=" 32 - 64 ppm" key="{4b7f1830-6d0a-4996-8bbc-fa64b67eb443}"/>
      <rule symbol="9" filter="&quot;FE&quot; > 64.000000 AND &quot;FE&quot; &lt;= 100.000000" label=" 64 - 100 ppm" key="{0ab8e8ea-fb35-4585-946a-f5a009af6ba3}"/>
      <rule symbol="10" filter="&quot;FE&quot; > 100.000000 AND &quot;FE&quot; &lt;= 1000.000000" label=" 100 - 1000 ppm" key="{27be7326-aee5-41f1-ab53-bea9218db005}"/>
    </rules>
    <symbols>
      <symbol name="0" type="fill" alpha="1" force_rhr="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleFill" enabled="1" locked="0">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color" type="QString" value="145,131,89,255"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="0,0,0,255"/>
            <Option name="outline_style" type="QString" value="no"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style" type="QString" value="diagonal_x"/>
          </Option>
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="145,131,89,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_style" v="no"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="diagonal_x"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="1" type="fill" alpha="1" force_rhr="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleFill" enabled="1" locked="0">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color" type="QString" value="144,229,230,255"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="0,0,0,255"/>
            <Option name="outline_style" type="QString" value="no"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="144,229,230,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_style" v="no"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="10" type="fill" alpha="1" force_rhr="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleFill" enabled="1" locked="0">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color" type="QString" value="212,120,0,255"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="0,0,0,255"/>
            <Option name="outline_style" type="QString" value="no"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="212,120,0,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_style" v="no"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="2" type="fill" alpha="1" force_rhr="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleFill" enabled="1" locked="0">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color" type="QString" value="140,231,176,255"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="0,0,0,255"/>
            <Option name="outline_style" type="QString" value="no"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="140,231,176,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_style" v="no"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="3" type="fill" alpha="1" force_rhr="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleFill" enabled="1" locked="0">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color" type="QString" value="135,233,121,255"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="0,0,0,255"/>
            <Option name="outline_style" type="QString" value="no"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="135,233,121,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_style" v="no"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="4" type="fill" alpha="1" force_rhr="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleFill" enabled="1" locked="0">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color" type="QString" value="162,225,91,255"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="0,0,0,255"/>
            <Option name="outline_style" type="QString" value="no"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="162,225,91,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_style" v="no"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="5" type="fill" alpha="1" force_rhr="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleFill" enabled="1" locked="0">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color" type="QString" value="199,214,70,255"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="0,0,0,255"/>
            <Option name="outline_style" type="QString" value="no"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="199,214,70,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_style" v="no"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="6" type="fill" alpha="1" force_rhr="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleFill" enabled="1" locked="0">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color" type="QString" value="218,198,58,255"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="0,0,0,255"/>
            <Option name="outline_style" type="QString" value="no"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="218,198,58,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_style" v="no"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="7" type="fill" alpha="1" force_rhr="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleFill" enabled="1" locked="0">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color" type="QString" value="218,177,56,255"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="0,0,0,255"/>
            <Option name="outline_style" type="QString" value="no"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="218,177,56,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_style" v="no"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="8" type="fill" alpha="1" force_rhr="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleFill" enabled="1" locked="0">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color" type="QString" value="216,158,40,255"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="0,0,0,255"/>
            <Option name="outline_style" type="QString" value="no"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="216,158,40,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_style" v="no"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="9" type="fill" alpha="1" force_rhr="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleFill" enabled="1" locked="0">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color" type="QString" value="214,139,20,255"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="0,0,0,255"/>
            <Option name="outline_style" type="QString" value="no"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="214,139,20,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_style" v="no"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style previewBkgrdColor="255,255,255,255" multilineHeight="1" legendString="Aa" fontItalic="0" fieldName="case&#xd;&#xa;when fe >0 &#xd;&#xa;then&#xd;&#xa;round(FE,2) ||  'mg/Kg'&#xd;&#xa;else&#xd;&#xa;'N/D'&#xd;&#xa;end" blendMode="0" fontLetterSpacing="0" fontUnderline="0" fontWordSpacing="0" fontKerning="1" textColor="50,50,50,255" namedStyle="Black" fontWeight="87" isExpression="1" useSubstitutions="0" allowHtml="0" capitalization="0" fontStrikeout="0" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontSize="8" fontSizeUnit="Point" textOpacity="1" fontFamily="Arial" textOrientation="horizontal">
        <families/>
        <text-buffer bufferDraw="1" bufferBlendMode="0" bufferColor="250,250,250,255" bufferOpacity="1" bufferJoinStyle="128" bufferSizeUnits="MM" bufferNoFill="1" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferSize="1"/>
        <text-mask maskEnabled="0" maskOpacity="1" maskType="0" maskSizeMapUnitScale="3x:0,0,0,0,0,0" maskSize="0" maskSizeUnits="MM" maskJoinStyle="128" maskedSymbolLayers=""/>
        <background shapeOffsetUnit="Point" shapeSVGFile="" shapeSizeUnit="Point" shapeRadiiUnit="Point" shapeBorderColor="128,128,128,255" shapeBorderWidth="0" shapeOffsetX="0" shapeSizeType="0" shapeType="0" shapeBorderWidthUnit="Point" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeFillColor="255,255,255,255" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetY="0" shapeRadiiX="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeSizeX="0" shapeBlendMode="0" shapeSizeY="0" shapeJoinStyle="64" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeDraw="0" shapeOpacity="1" shapeRadiiY="0" shapeRotationType="0" shapeRotation="0">
          <symbol name="markerSymbol" type="marker" alpha="1" force_rhr="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" type="QString" value=""/>
                <Option name="properties"/>
                <Option name="type" type="QString" value="collection"/>
              </Option>
            </data_defined_properties>
            <layer pass="0" class="SimpleMarker" enabled="1" locked="0">
              <Option type="Map">
                <Option name="angle" type="QString" value="0"/>
                <Option name="cap_style" type="QString" value="square"/>
                <Option name="color" type="QString" value="183,72,75,255"/>
                <Option name="horizontal_anchor_point" type="QString" value="1"/>
                <Option name="joinstyle" type="QString" value="bevel"/>
                <Option name="name" type="QString" value="circle"/>
                <Option name="offset" type="QString" value="0,0"/>
                <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="offset_unit" type="QString" value="MM"/>
                <Option name="outline_color" type="QString" value="35,35,35,255"/>
                <Option name="outline_style" type="QString" value="solid"/>
                <Option name="outline_width" type="QString" value="0"/>
                <Option name="outline_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="outline_width_unit" type="QString" value="MM"/>
                <Option name="scale_method" type="QString" value="diameter"/>
                <Option name="size" type="QString" value="2"/>
                <Option name="size_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="size_unit" type="QString" value="MM"/>
                <Option name="vertical_anchor_point" type="QString" value="1"/>
              </Option>
              <prop k="angle" v="0"/>
              <prop k="cap_style" v="square"/>
              <prop k="color" v="183,72,75,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="35,35,35,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="diameter"/>
              <prop k="size" v="2"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" type="QString" value=""/>
                  <Option name="properties"/>
                  <Option name="type" type="QString" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol name="fillSymbol" type="fill" alpha="1" force_rhr="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" type="QString" value=""/>
                <Option name="properties"/>
                <Option name="type" type="QString" value="collection"/>
              </Option>
            </data_defined_properties>
            <layer pass="0" class="SimpleFill" enabled="1" locked="0">
              <Option type="Map">
                <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="color" type="QString" value="255,255,255,255"/>
                <Option name="joinstyle" type="QString" value="bevel"/>
                <Option name="offset" type="QString" value="0,0"/>
                <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="offset_unit" type="QString" value="MM"/>
                <Option name="outline_color" type="QString" value="128,128,128,255"/>
                <Option name="outline_style" type="QString" value="no"/>
                <Option name="outline_width" type="QString" value="0"/>
                <Option name="outline_width_unit" type="QString" value="Point"/>
                <Option name="style" type="QString" value="solid"/>
              </Option>
              <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="color" v="255,255,255,255"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="128,128,128,255"/>
              <prop k="outline_style" v="no"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_unit" v="Point"/>
              <prop k="style" v="solid"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" type="QString" value=""/>
                  <Option name="properties"/>
                  <Option name="type" type="QString" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </background>
        <shadow shadowRadiusAlphaOnly="0" shadowDraw="0" shadowRadius="1.5" shadowRadiusUnit="MM" shadowBlendMode="6" shadowOffsetGlobal="1" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetDist="1" shadowColor="0,0,0,255" shadowOffsetUnit="MM" shadowScale="100" shadowUnder="0" shadowOffsetAngle="135" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowOpacity="0.69999999999999996"/>
        <dd_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format wrapChar="" useMaxLineLengthForAutoWrap="1" addDirectionSymbol="0" leftDirectionSymbol="&lt;" rightDirectionSymbol=">" formatNumbers="0" multilineAlign="3" placeDirectionSymbol="0" decimals="3" autoWrapLength="0" plussign="0" reverseDirectionSymbol="0"/>
      <placement predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" overrunDistance="0" overrunDistanceUnit="MM" layerType="PolygonGeometry" repeatDistance="0" geometryGeneratorType="PointGeometry" offsetUnits="MM" yOffset="0" preserveRotation="1" geometryGenerator="" rotationUnit="AngleDegrees" fitInPolygonOnly="0" polygonPlacementFlags="2" quadOffset="4" centroidInside="1" centroidWhole="0" offsetType="0" placementFlags="10" rotationAngle="0" xOffset="0" repeatDistanceUnits="MM" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" placement="0" distUnits="MM" distMapUnitScale="3x:0,0,0,0,0,0" maxCurvedCharAngleOut="-25" lineAnchorType="0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" dist="0" lineAnchorClipping="0" priority="5" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" maxCurvedCharAngleIn="25" lineAnchorPercent="0.5" geometryGeneratorEnabled="0"/>
      <rendering scaleMax="0" fontMinPixelSize="3" minFeatureSize="0" limitNumLabels="0" fontMaxPixelSize="10000" obstacleFactor="1" obstacleType="1" labelPerPart="0" drawLabels="1" mergeLines="0" maxNumLabels="2000" obstacle="1" scaleVisibility="0" scaleMin="0" upsidedownLabels="0" zIndex="0" fontLimitPixelSize="0" displayAll="0" unplacedVisibility="0"/>
      <dd_properties>
        <Option type="Map">
          <Option name="name" type="QString" value=""/>
          <Option name="properties"/>
          <Option name="type" type="QString" value="collection"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option name="anchorPoint" type="QString" value="pole_of_inaccessibility"/>
          <Option name="blendMode" type="int" value="0"/>
          <Option name="ddProperties" type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
          <Option name="drawToAllParts" type="bool" value="false"/>
          <Option name="enabled" type="QString" value="0"/>
          <Option name="labelAnchorPoint" type="QString" value="point_on_exterior"/>
          <Option name="lineSymbol" type="QString" value="&lt;symbol name=&quot;symbol&quot; type=&quot;line&quot; alpha=&quot;1&quot; force_rhr=&quot;0&quot; clip_to_extent=&quot;1&quot;>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;name&quot; type=&quot;QString&quot; value=&quot;&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option name=&quot;type&quot; type=&quot;QString&quot; value=&quot;collection&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;layer pass=&quot;0&quot; class=&quot;SimpleLine&quot; enabled=&quot;1&quot; locked=&quot;0&quot;>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;align_dash_pattern&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;capstyle&quot; type=&quot;QString&quot; value=&quot;square&quot;/>&lt;Option name=&quot;customdash&quot; type=&quot;QString&quot; value=&quot;5;2&quot;/>&lt;Option name=&quot;customdash_map_unit_scale&quot; type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot;/>&lt;Option name=&quot;customdash_unit&quot; type=&quot;QString&quot; value=&quot;MM&quot;/>&lt;Option name=&quot;dash_pattern_offset&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;dash_pattern_offset_map_unit_scale&quot; type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot;/>&lt;Option name=&quot;dash_pattern_offset_unit&quot; type=&quot;QString&quot; value=&quot;MM&quot;/>&lt;Option name=&quot;draw_inside_polygon&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;joinstyle&quot; type=&quot;QString&quot; value=&quot;bevel&quot;/>&lt;Option name=&quot;line_color&quot; type=&quot;QString&quot; value=&quot;60,60,60,255&quot;/>&lt;Option name=&quot;line_style&quot; type=&quot;QString&quot; value=&quot;solid&quot;/>&lt;Option name=&quot;line_width&quot; type=&quot;QString&quot; value=&quot;0.3&quot;/>&lt;Option name=&quot;line_width_unit&quot; type=&quot;QString&quot; value=&quot;MM&quot;/>&lt;Option name=&quot;offset&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;offset_map_unit_scale&quot; type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot;/>&lt;Option name=&quot;offset_unit&quot; type=&quot;QString&quot; value=&quot;MM&quot;/>&lt;Option name=&quot;ring_filter&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;trim_distance_end&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;trim_distance_end_map_unit_scale&quot; type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot;/>&lt;Option name=&quot;trim_distance_end_unit&quot; type=&quot;QString&quot; value=&quot;MM&quot;/>&lt;Option name=&quot;trim_distance_start&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;trim_distance_start_map_unit_scale&quot; type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot;/>&lt;Option name=&quot;trim_distance_start_unit&quot; type=&quot;QString&quot; value=&quot;MM&quot;/>&lt;Option name=&quot;tweak_dash_pattern_on_corners&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;use_custom_dash&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;width_map_unit_scale&quot; type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot;/>&lt;/Option>&lt;prop k=&quot;align_dash_pattern&quot; v=&quot;0&quot;/>&lt;prop k=&quot;capstyle&quot; v=&quot;square&quot;/>&lt;prop k=&quot;customdash&quot; v=&quot;5;2&quot;/>&lt;prop k=&quot;customdash_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;customdash_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;dash_pattern_offset&quot; v=&quot;0&quot;/>&lt;prop k=&quot;dash_pattern_offset_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;dash_pattern_offset_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;draw_inside_polygon&quot; v=&quot;0&quot;/>&lt;prop k=&quot;joinstyle&quot; v=&quot;bevel&quot;/>&lt;prop k=&quot;line_color&quot; v=&quot;60,60,60,255&quot;/>&lt;prop k=&quot;line_style&quot; v=&quot;solid&quot;/>&lt;prop k=&quot;line_width&quot; v=&quot;0.3&quot;/>&lt;prop k=&quot;line_width_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;offset&quot; v=&quot;0&quot;/>&lt;prop k=&quot;offset_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;offset_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;ring_filter&quot; v=&quot;0&quot;/>&lt;prop k=&quot;trim_distance_end&quot; v=&quot;0&quot;/>&lt;prop k=&quot;trim_distance_end_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;trim_distance_end_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;trim_distance_start&quot; v=&quot;0&quot;/>&lt;prop k=&quot;trim_distance_start_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;trim_distance_start_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;tweak_dash_pattern_on_corners&quot; v=&quot;0&quot;/>&lt;prop k=&quot;use_custom_dash&quot; v=&quot;0&quot;/>&lt;prop k=&quot;width_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;name&quot; type=&quot;QString&quot; value=&quot;&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option name=&quot;type&quot; type=&quot;QString&quot; value=&quot;collection&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>"/>
          <Option name="minLength" type="double" value="0"/>
          <Option name="minLengthMapUnitScale" type="QString" value="3x:0,0,0,0,0,0"/>
          <Option name="minLengthUnit" type="QString" value="MM"/>
          <Option name="offsetFromAnchor" type="double" value="0"/>
          <Option name="offsetFromAnchorMapUnitScale" type="QString" value="3x:0,0,0,0,0,0"/>
          <Option name="offsetFromAnchorUnit" type="QString" value="MM"/>
          <Option name="offsetFromLabel" type="double" value="0"/>
          <Option name="offsetFromLabelMapUnitScale" type="QString" value="3x:0,0,0,0,0,0"/>
          <Option name="offsetFromLabelUnit" type="QString" value="MM"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <customproperties>
    <Option type="Map">
      <Option name="QFieldSync/action" type="QString" value="offline"/>
      <Option name="QFieldSync/cloud_action" type="QString" value="offline"/>
      <Option name="QFieldSync/photo_naming" type="QString" value="{}"/>
      <Option name="dualview/previewExpressions" type="List">
        <Option type="QString" value="lote || '-' ||segmento"/>
      </Option>
      <Option name="embeddedWidgets/count" type="QString" value="0"/>
      <Option name="subset_expression" type="QString" value="&quot;idlotecampania&quot; in (366, 371, 361, 368, 370, 363, 362, 369, 367)"/>
      <Option name="subset_expression_checked" type="int" value="0"/>
      <Option name="variableNames"/>
      <Option name="variableValues"/>
    </Option>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>0.7</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory minScaleDenominator="0" height="15" width="15" direction="1" minimumSize="0" labelPlacementMethod="XHeight" backgroundAlpha="255" scaleBasedVisibility="0" diagramOrientation="Up" spacingUnit="MM" sizeType="MM" rotationOffset="270" spacing="0" enabled="0" lineSizeScale="3x:0,0,0,0,0,0" showAxis="0" lineSizeType="MM" penColor="#000000" scaleDependency="Area" maxScaleDenominator="1e+08" backgroundColor="#ffffff" penAlpha="255" spacingUnitScale="3x:0,0,0,0,0,0" opacity="1" sizeScale="3x:0,0,0,0,0,0" barWidth="5" penWidth="0">
      <fontProperties style="" description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0"/>
      <attribute color="#000000" colorOpacity="1" label="" field=""/>
      <axisSymbol>
        <symbol name="" type="line" alpha="1" force_rhr="0" clip_to_extent="1">
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
          <layer pass="0" class="SimpleLine" enabled="1" locked="0">
            <Option type="Map">
              <Option name="align_dash_pattern" type="QString" value="0"/>
              <Option name="capstyle" type="QString" value="square"/>
              <Option name="customdash" type="QString" value="5;2"/>
              <Option name="customdash_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
              <Option name="customdash_unit" type="QString" value="MM"/>
              <Option name="dash_pattern_offset" type="QString" value="0"/>
              <Option name="dash_pattern_offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
              <Option name="dash_pattern_offset_unit" type="QString" value="MM"/>
              <Option name="draw_inside_polygon" type="QString" value="0"/>
              <Option name="joinstyle" type="QString" value="bevel"/>
              <Option name="line_color" type="QString" value="35,35,35,255"/>
              <Option name="line_style" type="QString" value="solid"/>
              <Option name="line_width" type="QString" value="0.26"/>
              <Option name="line_width_unit" type="QString" value="MM"/>
              <Option name="offset" type="QString" value="0"/>
              <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
              <Option name="offset_unit" type="QString" value="MM"/>
              <Option name="ring_filter" type="QString" value="0"/>
              <Option name="trim_distance_end" type="QString" value="0"/>
              <Option name="trim_distance_end_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
              <Option name="trim_distance_end_unit" type="QString" value="MM"/>
              <Option name="trim_distance_start" type="QString" value="0"/>
              <Option name="trim_distance_start_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
              <Option name="trim_distance_start_unit" type="QString" value="MM"/>
              <Option name="tweak_dash_pattern_on_corners" type="QString" value="0"/>
              <Option name="use_custom_dash" type="QString" value="0"/>
              <Option name="width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            </Option>
            <prop k="align_dash_pattern" v="0"/>
            <prop k="capstyle" v="square"/>
            <prop k="customdash" v="5;2"/>
            <prop k="customdash_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="customdash_unit" v="MM"/>
            <prop k="dash_pattern_offset" v="0"/>
            <prop k="dash_pattern_offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="dash_pattern_offset_unit" v="MM"/>
            <prop k="draw_inside_polygon" v="0"/>
            <prop k="joinstyle" v="bevel"/>
            <prop k="line_color" v="35,35,35,255"/>
            <prop k="line_style" v="solid"/>
            <prop k="line_width" v="0.26"/>
            <prop k="line_width_unit" v="MM"/>
            <prop k="offset" v="0"/>
            <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="offset_unit" v="MM"/>
            <prop k="ring_filter" v="0"/>
            <prop k="trim_distance_end" v="0"/>
            <prop k="trim_distance_end_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="trim_distance_end_unit" v="MM"/>
            <prop k="trim_distance_start" v="0"/>
            <prop k="trim_distance_start_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="trim_distance_start_unit" v="MM"/>
            <prop k="tweak_dash_pattern_on_corners" v="0"/>
            <prop k="use_custom_dash" v="0"/>
            <prop k="width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" type="QString" value=""/>
                <Option name="properties"/>
                <Option name="type" type="QString" value="collection"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
      </axisSymbol>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings zIndex="0" placement="1" showAll="1" obstacle="0" linePlacementFlags="18" dist="0" priority="0">
    <properties>
      <Option type="Map">
        <Option name="name" type="QString" value=""/>
        <Option name="properties"/>
        <Option name="type" type="QString" value="collection"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
    <activeChecks/>
    <checkConfiguration type="Map">
      <Option name="QgsGeometryGapCheck" type="Map">
        <Option name="allowedGapsBuffer" type="double" value="0"/>
        <Option name="allowedGapsEnabled" type="bool" value="false"/>
        <Option name="allowedGapsLayer" type="QString" value=""/>
      </Option>
    </checkConfiguration>
  </geometryOptions>
  <legend type="default-vector" showLabelLegend="0"/>
  <referencedLayers/>
  <fieldConfiguration>
    <field name="id" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="segmento" configurationFlags="None">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="ceap" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias name="" index="0" field="id"/>
    <alias name="" index="1" field="segmento"/>
    <alias name="" index="2" field="ceap"/>
  </aliases>
  <defaults>
    <default expression="" applyOnUpdate="0" field="id"/>
    <default expression="" applyOnUpdate="0" field="segmento"/>
    <default expression="" applyOnUpdate="0" field="ceap"/>
  </defaults>
  <constraints>
    <constraint exp_strength="0" constraints="3" unique_strength="1" notnull_strength="1" field="id"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0" field="segmento"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0" field="ceap"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" exp="" field="id"/>
    <constraint desc="" exp="" field="segmento"/>
    <constraint desc="" exp="" field="ceap"/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig sortExpression="&quot;cod_control&quot;" sortOrder="0" actionWidgetStyle="dropDown">
    <columns>
      <column type="actions" hidden="1" width="-1"/>
      <column name="segmento" type="field" hidden="0" width="100"/>
      <column name="ceap" type="field" hidden="0" width="100"/>
      <column name="id" type="field" hidden="0" width="100"/>
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
