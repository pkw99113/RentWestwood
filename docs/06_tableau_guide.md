# 6단계. Tableau Public 대시보드 만들기

데이터: `data/tableau/` (만들기: `python scripts/06_tableau_export.py`)

| 파일 | 한 줄 = | 용도 |
| --- | --- | --- |
| `scenario_costs.csv` | 유형 × 렌트 추정 방식 × 여름 계획 × 선택지 (360행) | 비용 비교, 승률 |
| `rent_trend.csv` | 월 × 지역 | 렌트 추이 |
| `commute_breakeven.csv` | 유형 | 통학 손익분기 |

## 대시보드 구성 (보는 순서: 결론 → 근거 → 추세)

**제목**: "여름에 LA를 떠나면 UCLA 아파트, 4명이 서브렛하면 West LA가 가장 싸다"
(분석 내용이 아니라 결론을 제목에 쓴다. 의사결정자는 대시보드를 몇 초만 본다.)

**필터 (상단 한 줄)**: `summer_plan_label`, `group_size`, `rent_method_label`(기본값: Main)

### 시트 1. 선택지별 1인당 연간 비용 (왼쪽 위)
- 데이터: `scenario_costs.csv`
- 열: `option`, 행: `AVG(annual_cost)`, 막대 그래프
- 필터: 위 세 필터 적용. `unit_type`도 필터로 두고 기본값 `2/4 apartment`
- 색상: UCLA `#1baf7a`, West LA `#eb6834`, Westwood `#2a78d6` (레포 차트와 동일)
- 레이블: 막대 끝에 금액 표시 (`$#,##0`)

### 시트 2. UCLA가 가장 싼 시나리오 비율 (오른쪽 위)
- 데이터: `scenario_costs.csv`, 필터 `option = UCLA`
- 계산된 필드: `UCLA win share` = `SUM([is_cheapest]) / COUNTD(STR([unit_type]) + [rent_method])`
- 행: `summer_plan_label`, 열: `UCLA win share`, 가로 막대
- 이 시트에는 `summer_plan_label` 필터를 적용하지 않는다 (다섯 계획을 모두 비교해야 하므로)

### 시트 3. 렌트 추이와 프리미엄 (아래)
- 데이터: `rent_trend.csv`
- 열: `month`(연속형, 월), 행: `rent`, 색상: `area` → 선 그래프
- 프리미엄은 **같은 축에 겹치지 말고** 아래에 별도 시트로 (`westwood_premium_pct`, 선 하나). 축이 두 개인 차트는 읽는 사람을 헷갈리게 한다.
- 선 끝에 지역 이름과 최신 값 레이블

### 마무리
- 툴팁에 `rent_method_label`, `annual_cost`, `cost_rank` 포함
- 대시보드 하단에 데이터 출처와 기준 시점 한 줄: "Zillow ZORI (2026-10), HUD SAFMR FY2026, UCLA Housing 2026-27"
- 게시 후 링크를 README 맨 위와 이력서 제목 줄에 추가
