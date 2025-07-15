<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis maxScale="0" version="3.22.4-Białowieża" styleCategories="AllStyleCategories" hasScaleBasedVisibilityFlag="0" minScale="1e+08">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>0</Searchable>
    <Private>0</Private>
  </flags>
  <temporal enabled="0" fetchMode="0" mode="0">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <customproperties>
    <Option type="Map">
      <Option value="false" type="bool" name="WMSBackgroundLayer"/>
      <Option value="false" type="bool" name="WMSPublishDataSourceUrl"/>
      <Option value="transparency" type="QString" name="embeddedWidgets/0/id"/>
      <Option value="1" type="int" name="embeddedWidgets/count"/>
      <Option value="Value" type="QString" name="identify/format"/>
    </Option>
  </customproperties>
  <pipe-data-defined-properties>
    <Option type="Map">
      <Option value="" type="QString" name="name"/>
      <Option name="properties"/>
      <Option value="collection" type="QString" name="type"/>
    </Option>
  </pipe-data-defined-properties>
  <pipe>
    <provider>
      <resampling maxOversampling="2" zoomedOutResamplingMethod="nearestNeighbour" enabled="false" zoomedInResamplingMethod="nearestNeighbour"/>
    </provider>
    <rasterrenderer nodataColor="" band="1" type="paletted" alphaBand="-1" opacity="0.264">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <colorPalette>
        <paletteEntry value="0" label="0" color="#ff0000" alpha="255"/>
        <paletteEntry value="1" label="1" color="#fe4900" alpha="255"/>
        <paletteEntry value="2" label="2" color="#00fe00" alpha="255"/>
        <paletteEntry value="3" label="3" color="#ffffff" alpha="0"/>
        <paletteEntry value="4" label="4" color="#ffffff" alpha="0"/>
        <paletteEntry value="5" label="5" color="#ffffff" alpha="0"/>
        <paletteEntry value="6" label="6" color="#ffffff" alpha="0"/>
        <paletteEntry value="7" label="7" color="#ffffff" alpha="0"/>
        <paletteEntry value="8" label="8" color="#ffffff" alpha="0"/>
        <paletteEntry value="9" label="9" color="#ffffff" alpha="0"/>
        <paletteEntry value="10" label="10" color="#ffffff" alpha="0"/>
        <paletteEntry value="11" label="11" color="#ffffff" alpha="0"/>
        <paletteEntry value="12" label="12" color="#ffffff" alpha="0"/>
        <paletteEntry value="13" label="13" color="#ffffff" alpha="0"/>
        <paletteEntry value="14" label="14" color="#ffffff" alpha="0"/>
        <paletteEntry value="15" label="15" color="#ffffff" alpha="0"/>
      </colorPalette>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0" gamma="1"/>
    <huesaturation grayscaleMode="0" colorizeStrength="100" invertColors="0" colorizeRed="255" saturation="0" colorizeGreen="128" colorizeBlue="128" colorizeOn="0"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
