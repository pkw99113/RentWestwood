# 3단계. SQL로 1인당 비용 테이블 만들기

실행: `python scripts/03_run_sql.py` (DuckDB, `sql/` 폴더의 파일을 순서대로 실행하고 결과를 `data/processed/`에 저장)

## 범위 변경
분석 대상을 캠퍼스 인접 두 ZIP으로 좁혔다: **Westwood (90024)**, **West LA / Sawtelle (90025)**. 비교 기준은 UCLA University Apartments.
8개 ZIP은 ZORI와 SAFMR이 서로 일치하는지 확인하는 교차 검증에만 쓴다(ZIP 2개로는 상관계수를 낼 수 없기 때문).

## 핵심 판단: 두 출처를 결합한 추정 렌트
- SAFMR에서는 두 ZIP이 거의 같다 (1BR $3,450 vs $3,440). ZORI에서는 Westwood가 약 12% 비싸다 ($3,617 vs $3,229).
- SAFMR은 침실 수별 구조를 알려주지만 인접 ZIP 간 차이를 잘 구분하지 못하고, ZORI는 ZIP 간 차이를 보여주지만 침실 수 구분이 없다.
- 그래서 **ZIP의 수준은 ZORI에서, 침실 수에 따른 비율은 SAFMR에서** 가져왔다.
  `추정 렌트(zip, 침실) = 최신 ZORI(zip) × SAFMR(zip, 침실) / SAFMR(zip, 1BR)`
- 가정: ZORI ≈ 일반적인 1베드 렌트. 8개 ZIP 검증에서 ZORI ÷ SAFMR 1BR의 중앙값이 약 1.0이라 이 가정을 뒷받침한다.

## 쿼리 목록
| 파일 | 질문 | 핵심 SQL |
| --- | --- | --- |
| `01_load_tables.sql` | 데이터 적재 | `read_csv_auto`, 타입 지정 |
| `02_zori_trend.sql` | 렌트 추이와 Westwood 프리미엄 | `LAG(…, 12) OVER (PARTITION BY … ORDER BY …)`, `MAX(CASE WHEN …)` 피벗 |
| `03_market_rent_by_bedroom.sql` | ZIP × 침실 수 추정 렌트 | `QUALIFY ROW_NUMBER()`, 집계 없는 윈도우 함수 |
| `04_per_person_cost.sql` | UCLA vs 같은 구조의 외부 아파트 1인당 비용 | 침실 수 기준 `JOIN`, 파라미터 CTE, `UNION ALL`, `RANK()` |
| `05_commute_breakeven.sql` | 90025의 통학 시간은 렌트 절약만큼 가치가 있나 | 피벗 + 손익분기 계산 |

## 결과 (2026-10 기준)

**1) 추이**: Westwood 프리미엄은 2025년 가을 약 10%에서 2026년 5월 15%까지 커졌다가 10월 12%. 최근 1년 상승률 Westwood +2.6%, West LA +0.4%.

**2) 1인당 비용**: 어떤 기준으로 보느냐에 따라 결론이 뒤집힌다.

| 기준 | 가장 싼 선택 |
| --- | --- |
| 학기 중 월평균 | 대부분 **West LA**. UCLA는 9개월 계약이라 월 환산 비용이 높다 |
| 연간 총비용 (여름에 LA를 떠남) | 거의 모든 유형에서 **UCLA**. 외부 아파트는 12개월 계약이라 여름 월세도 낸다 |
| 연간 총비용 (여름 3개월 서브렛, 70% 회수) | 2베드 4인, 2베드 3인 등에서 **West LA**, 2베드 4인은 Westwood도 UCLA보다 쌈 |

예: 2베드 4인 기준 1인당 연간 비용은 UCLA $12,168, West LA $12,081(서브렛 시 $9,967), Westwood $13,524(서브렛 시 $11,157).

**3) 통학 손익분기**: West LA가 Westwood보다 월 $120~194 싸고, 추가 통학이 월 약 8시간(편도 15분 × 16일 가정)이라면, 시간 가치가 **시간당 $15~24**보다 높은 학생에게는 Westwood가 낫다.

## 한계
- 추정 렌트는 "ZORI ≈ 1베드 렌트" 가정에 의존한다. SAFMR 그대로 쓰면 두 ZIP 차이가 사라진다(보수적 대안으로 보고서에 함께 제시 예정).
- UCLA 계약 9개월, 서브렛 회수율 70%, 통학 시간은 가정값이며 `params` CTE에서 바꿀 수 있다.
- 외부 아파트의 1베드 3인 같은 구성은 현실에서 흔하지 않다. UCLA와 같은 조건 비교를 위해 기계적으로 맞춘 것이다.
- 보증금, 가구, 주차, 공과금 차이(UCLA 요금 포함 여부 미확인)는 아직 반영하지 않았다.
