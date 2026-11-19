# 6단계. Tableau Public 대시보드 만들기

데이터: `data/tableau/` (만들기: `python scripts/06_tableau_export.py`)

| 파일 | 한 줄 = | 용도 |
| --- | --- | --- |
| `scenario_costs.csv` | 유형 × 렌트 추정 × 여름 계획 × 통학 방식 × 시간 가치 × 선택지 (8,640행) | 비용 비교, 승률 |
| `rent_trend.csv` | 동네 × 월 | 렌트 추이 |
| `commute_cost.csv` | 동네 × 통학 수단 | 통학 시간·현금 비용 |
| `time_value_breakeven.csv` | 통학 방식 × 여름 계획 × 동네 | 손익분기 시간 가치 |

## 대시보드 구성 (보는 순서: 결론 → 근거 → 추세)

**제목**: "렌트는 Koreatown이 가장 싸지만, 통학 시간을 시급 $20로 보면 Palms·Westwood·UCLA 아파트가 이긴다"
(분석 내용이 아니라 결론을 제목에 쓴다. 의사결정자는 대시보드를 몇 초만 본다.)

**필터 (상단 한 줄)**: `summer_plan_label`, `car_profile_label`, `time_value_label`(기본값 $20/hr), `group_size`, `rent_method_label`(기본값: Main)

### 시트 1. 선택지별 1인당 연간 비용 (왼쪽 위)
- 데이터: `scenario_costs.csv`
- 행: `option`, 열: `AVG(annual_rent)`와 `AVG(annual_commute_cost)`를 쌓은 가로 막대 (렌트 + 통학)
- 필터: 위 세 필터 적용. `unit_type`도 필터로 두고 기본값 `2/4 apartment`
- 색상: 레포 차트와 같은 동네별 고정색 (`scripts/05_make_charts.py`의 COLOR 참고)
- 레이블: 막대 끝에 금액 표시 (`$#,##0`)

### 시트 2. 시간 가치별 가장 싼 선택 (오른쪽 위)
- 데이터: `scenario_costs.csv`, 필터 `is_cheapest = 1`
- 행: `time_value_label`, 열: `COUNT` 비율(구성 비율), 색상: `option` → 100% 누적 가로 막대
- 이 시트에는 `time_value_label` 필터를 적용하지 않는다 (세 값을 비교해야 하므로)

### 시트 3. 렌트 추이와 프리미엄 (아래)
- 데이터: `rent_trend.csv`
- 열: `month`(연속형, 월), 행: `rent`, 색상: `area` → 선 그래프
- Westwood 대비 비율(`pct_vs_westwood`)을 보여주고 싶으면 **같은 축에 겹치지 말고** 별도 시트로 만든다. 축이 두 개인 차트는 읽는 사람을 헷갈리게 한다.
- 선 끝에 지역 이름과 최신 값 레이블

### 마무리
- 툴팁에 `annual_rent`, `annual_commute_cost`, `annual_cost`, `cost_rank` 포함
- (선택) 시트 4: `time_value_breakeven.csv`로 동네별 손익분기 시간 가치 막대
- 대시보드 하단에 데이터 출처와 기준 시점 한 줄: "Zillow ZORI (2026-10), HUD SAFMR FY2026, UCLA Housing/Transportation 2026-27, AAA 2026, Google Maps (2026-11)"
- 게시 후 링크를 README 맨 위와 이력서 제목 줄에 추가
