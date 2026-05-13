# Sample Documents Index

Generated from `sample documents/` directory. State inferred from city names in filenames; tier inferred from page count (≥5 pages = high, 3–4 = medium, 1–2 = low) when not explicit in filename.

`?` = pdfplumber failed to count pages (encrypted or malformed).

## AZ — Arizona

| Filename | Size (KB) | Pages | Tier |
|---|---|---|---|
| sample_26_dust_5veh_phoenix.pdf | 13.7 | 5 | high |

## CA — California

| Filename | Size (KB) | Pages | Tier |
|---|---|---|---|
| sample_25_dui_wrongway_la.pdf | 14.8 | 5 | high |

## CO — Colorado

| Filename | Size (KB) | Pages | Tier |
|---|---|---|---|
| sample_23_blizzard_semi_denver.pdf | 14.7 | 5 | high |

## FL — Florida

| Filename | Size (KB) | Pages | Tier |
|---|---|---|---|
| sample_27_tropical_moto_tampa.pdf | 13.9 | 5 | high |

## GA — Georgia

| Filename | Size (KB) | Pages | Tier |
|---|---|---|---|
| sample_29_rain_5veh_atlanta.pdf | 14.2 | ? | unknown |

## IA — IA Report (synthetic)

| Filename | Size (KB) | Pages | Tier |
|---|---|---|---|
| IA_Report_High_Complexity.pdf | 1.6 | 1 | high |
| IA_Report_Low_Complexity.pdf | 1.5 | 1 | low |

## IL — Illinois

| Filename | Size (KB) | Pages | Tier |
|---|---|---|---|
| sample_30_ice_semi_chicago.pdf | 16.9 | 6 | high |

## MA — Massachusetts

| Filename | Size (KB) | Pages | Tier |
|---|---|---|---|
| sample_22_ice_bus_boston.pdf | 13.7 | 5 | high |

## MI — Michigan

| Filename | Size (KB) | Pages | Tier |
|---|---|---|---|
| sample_32_ice_semi_detroit.pdf | 14.8 | 5 | high |

## MN — Minnesota

| Filename | Size (KB) | Pages | Tier |
|---|---|---|---|
| sample_28_blizzard_6veh_minneapolis.pdf | 14.7 | 5 | high |

## NY — New York

| Filename | Size (KB) | Pages | Tier |
|---|---|---|---|
| sample_24_rain_ped_nyc.pdf | 14.1 | 5 | high |

## PA — Pennsylvania

| Filename | Size (KB) | Pages | Tier |
|---|---|---|---|
| sample_33_ice_ped_philadelphia.pdf | 15.0 | 5 | high |

## TX — Texas

| Filename | Size (KB) | Pages | Tier |
|---|---|---|---|
| sample_21_fog_5veh_houston.pdf | 14.4 | 5 | high |
| sample_31_hail_5veh_dallas.pdf | 13.9 | ? | unknown |
| sample_35_flood_6veh_sanantonio.pdf | 14.9 | 5 | high |
| sample_full_report.pdf | 27.2 | 9 | high |
| sample_full_report_dupes.pdf | 29.3 | 10 | high |

## WA — Washington

| Filename | Size (KB) | Pages | Tier |
|---|---|---|---|
| sample_34_fog_bridge_seattle.pdf | 13.9 | 5 | high |

## Unknown state (numbered sequence — no city in filename)

| Filename | Size (KB) | Pages | Tier |
|---|---|---|---|
| Police_Report_High_Complexity.pdf | 1.6 | 1 | high |
| Police_Report_Low_Complexity.pdf | 1.4 | 1 | low |
| Police_Report_Medium_Complexity.pdf | 1.5 | 1 | medium |
| sample_01_snow_noinj.pdf | 5.9 | 2 | low |
| sample_02_fog_minor.pdf | 6.7 | 2 | low |
| sample_03_clear_noinj.pdf | 5.8 | 2 | low |
| sample_04_rain_serious.pdf | 11.0 | 4 | medium |
| sample_05_ice_minor.pdf | 6.5 | ? | unknown |
| sample_06_clear_ped.pdf | 6.7 | 2 | low |
| sample_07_rain_injury.pdf | 6.8 | 2 | low |
| sample_08_fog_chain.pdf | 10.1 | 3 | medium |
| sample_09_clear_noinj.pdf | 5.8 | 2 | low |
| sample_10_rain_moderate.pdf | 6.8 | 2 | low |
| sample_11_snow_serious.pdf | 7.1 | 2 | low |
| sample_12_clear_bicycle.pdf | 6.9 | 2 | low |
| sample_13_fog_noinj.pdf | 5.9 | 2 | low |
| sample_14_rain_multi.pdf | 10.2 | 3 | medium |
| sample_15_clear_rollover.pdf | 6.8 | 2 | low |
| sample_16_ice_chain.pdf | 12.0 | 4 | medium |
| sample_17_clear_noinj.pdf | 5.7 | 2 | low |
| sample_18_rain_minor.pdf | 6.6 | 2 | low |
| sample_19_clear_serious.pdf | 7.4 | 2 | low |
| sample_20_snow_noinj.pdf | 5.9 | 2 | low |

---

**Total: 42 documents** (40 police reports + 2 IA reports)

**Recommended ground-truth labeling candidates** (one high-complexity doc per major state, best coverage of form variants):

| Priority | Filename | State | Form ID | Rationale |
|---|---|---|---|---|
| 1 | `sample_full_report.pdf` | TX | tx_cr3 | 9 pages, highest field density |
| 2 | `sample_25_dui_wrongway_la.pdf` | CA | ca_chp555 | 5 pages, CHP 555 form |
| 3 | `sample_24_rain_ped_nyc.pdf` | NY | ny_mv104a | 5 pages, NY MV-104A form |
| 4 | `sample_27_tropical_moto_tampa.pdf` | FL | fl_hsmv | 5 pages, FL HSMV form |
| 5 | `sample_33_ice_ped_philadelphia.pdf` | PA | pa_aa600 | 5 pages, PA AA-600 form |
