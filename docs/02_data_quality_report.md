# 2단계. 데이터 품질 점검 결과 (자동 생성)

`scripts/02_extract_study_area.py` 실행 결과. 해석은 `docs/02_data_collection.md` 참고.

## ZORI (Zillow Observed Rent Index)
- Raw file: 8,355 ZIPs, 142 months (2015-01-31 to 2026-10-31)
- Duplicate ZIP rows: 0
- Study ZIPs found: 2 of 2
- Months with data per ZIP (missing months are blank in the source, i.e. not enough listings):

| ZIP | Area | First month | Last month | Months with data | Missing |
| --- | --- | --- | --- | --- | --- |
| 90024 | Westwood | 2015-01 | 2026-10 | 142 | 0 |
| 90025 | West LA / Sawtelle | 2015-01 | 2026-10 | 142 | 0 |

## HUD Small Area Fair Market Rents, FY2026 (revised)
- Raw file: 51,895 rows, 38,601 unique ZIPs
- ZIPs listed in more than one HUD area: 10,106 (a ZIP can cross metro boundaries)
- Study ZIPs found: 2 of 2, rows: 2
- HUD areas for study ZIPs: Los Angeles-Long Beach-Glendale, CA HUD Metro FMR Area
- Missing SAFMR values: 0

## Cross-check: ZORI (2026-10) vs SAFMR, validation set of 8 West/Central LA ZIPs
ZORI is a typical market rent across all unit sizes; SAFMR is HUD's 40th-percentile rent (rent + utilities) by bedroom count.
If ZORI sits between the 1BR and 2BR SAFMR, the two sources are telling a consistent story.

| ZIP | Area | ZORI | SAFMR 1BR | SAFMR 2BR | ZORI / SAFMR 1BR |
| --- | --- | --- | --- | --- | --- |
| 90024 | Westwood | $3,617 | $3,450 | $4,300 | 1.05 |
| 90025 | West LA / Sawtelle | $3,229 | $3,440 | $4,290 | 0.94 |
| 90064 | Rancho Park | $3,561 | $3,490 | $4,350 | 1.02 |
| 90049 | Brentwood | $3,898 | $3,490 | $4,350 | 1.12 |
| 90034 | Palms | $2,746 | $2,870 | $3,580 | 0.96 |
| 90066 | Mar Vista | $3,049 | $2,840 | $3,540 | 1.07 |
| 90005 | Koreatown (90005) | $2,446 | $2,510 | $3,130 | 0.97 |
| 90020 | Koreatown (90020) | $1,878 | $2,460 | $3,070 | 0.76 |

- Correlation between ZORI and SAFMR 1BR across the validation ZIPs: 0.93
