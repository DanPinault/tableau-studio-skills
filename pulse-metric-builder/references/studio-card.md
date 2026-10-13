# Pulse cards on a Studio dashboard

Studio has a built-in **Pulse Metric** dashboard object
(`com.tableau.pulse-metric`, extension version 0.100.0). Each card points at one
metric (`METRIC_ID`), so the period is fixed by the metric you created.

## Option A — let the user place it (always works)

1. Make sure the metric's published data source is connected in the workbook.
2. In the dashboard, drag **Pulse Metric** from the Objects pane onto the canvas.
3. In its setup, pick the metric by name (from `create` results).
4. Repeat per card. Give the user the metric names and `pulse_url`s.

## Option B — write the zone XML (verified working; preferred when the agent can edit the document)

Verified end to end: the cards rendered with live values in Desktop, the workbook
saved cleanly, and the cards worked after publishing to Tableau Cloud. Typical
layout: a strip of cards directly under the title zone (about 14% of the height,
width split evenly across the cards), with the existing chart zones shifted down
and shortened to make room. `referenced-view instances` must equal the card count
on that dashboard; add one `referenced-view` per dashboard.

Use the `studio_card_settings` from `create` for the `<setting>` rows. Use a
fresh 32-hex-char uppercase `instance-id` per card. `x/y/w/h` are in
dashboard units (0–100000 of the dashboard's width/height).

```xml
<zone type-v2='dashboard-object' forceUpdate='true' id='<new zone id>'
      x='..' y='..' w='..' h='..'
      param='[com.tableau.pulse-metric].[0.100.0].[tableau:/pulse/extension-assets/dashboard-metric/index.html]'>
  <add-in add-in-id='com.tableau.pulse-metric'
          extension-url='tableau:/pulse/extension-assets/dashboard-metric/index.html'
          extension-version='0.100.0' instance-id='<32 HEX>'>
    <instance-settings>
      <setting key='DATASOURCE_NAME' value='<workbook data source name>' />
      <setting key='ENABLE_LINK' value='true' />
      <setting key='MEASURE_FIELD' value='<measure>' />
      <setting key='METRIC_DEFINITION_ID' value='<definition id>' />
      <setting key='METRIC_ID' value='<metric id>' />
      <setting key='PULSE_ROOT' value='https://<pod>/pulse/site/<site>/' />
      <setting key='SQUARE_CORNERS' value='true' />
      <setting key='SYSTEM_TOOLTIP_TEXT' value='Year to Date' />
      <setting key='TIME_DIMENSION_FIELD' value='<time field>' />
      <setting key='USE_DASHBOARD_FILTERS' value='true' />
      <setting key='USE_FULL_CARD' value='false' />
      <setting key='has_been_configured' value='true' />
      <setting key='has_been_initialized' value='true' />
    </instance-settings>
    <type-settings>
      <dashboard />
    </type-settings>
  </add-in>
</zone>
```

The workbook also needs this manifest block once, right after `</windows>`,
with one `<referenced-view>` per dashboard that has cards (`instances` = card
count on it):

```xml
  <referenced-extensions>
    <referenced-extension>
      <manifest manifest-version='0.1'>
        <dashboard-extension extension-version='0.100.0' id='com.tableau.pulse-metric'>
          <default-locale>en_US</default-locale>
          <name resource-id='name' />
          <description>Display Tableau Pulse metric</description>
          <author email='customerservice@tableau.com' name='Tableau' organization='Tableau' website='https://www.tableau.com' />
          <min-api-version>1.10</min-api-version>
          <source-location>
            <url>tableau:/pulse/extension-assets/dashboard-metric/index.html</url>
          </source-location>
          <icon />
          <context-menu>
            <configure-context-menu-item />
          </context-menu>
        </dashboard-extension>
        <resources>
          <resource id='name'>
            <text locale='de_DE'>Pulse-Metrik</text>
            <text locale='en_GB'>Pulse Metric</text>
            <text locale='en_US'>Pulse Metric</text>
            <text locale='es_ES'>Métrica de Pulse</text>
            <text locale='fr_CA'>Métrique Pulse</text>
            <text locale='fr_FR'>Métrique Pulse</text>
            <text locale='it_IT'>Metrica di Pulse</text>
            <text locale='ja_JP'>Pulse Metric</text>
            <text locale='ko_KR'>Pulse 메트릭</text>
            <text locale='nl_NL'>Pulse-statistiek</text>
            <text locale='pt_BR'>Métrica do Pulse</text>
            <text locale='sv_SE'>Pulse-mätvärde</text>
            <text locale='th_TH'>มตริก Pulse</text>
            <text locale='zh_CN'>Pulse 指标</text>
            <text locale='zh_TW'>Pulse 指標</text>
          </resource>
        </resources>
      </manifest>
      <referenced-views>
        <referenced-view instances='<n>' viewId='<dashboard name>' />
      </referenced-views>
    </referenced-extension>
  </referenced-extensions>
```

Gotchas when applying by document:
- Add `<Extensions />` to the document-format-change-manifest (keep that list
  alphabetical), or validate rejects the add-in.
- A brand-new dashboard window needs `<viewpoints />`, `<active>`, and
  `<device-preview>`, or validate rejects it.
- Apply the whole workbook document (GET document → splice → validate → POST),
  not a per-dashboard patch; per-dashboard applies fail on sheet references.
- Dashboard image export returns 500 when Pulse zones are present; screenshot
  the window to check the result instead.
- Cards keep working after the workbook is published to Tableau Cloud.

`DATASOURCE_NAME` is the data source's name inside the workbook. For a
published data source connection Studio uses its content URL (the script's
default); check it against the workbook's data source list.
