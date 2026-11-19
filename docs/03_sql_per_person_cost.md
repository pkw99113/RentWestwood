# 3단계. SQL로 1인당 비용과 통학 비용 테이블 만들기

실행: `python scripts/03_run_sql.py` (DuckDB, `sql/` 폴더의 파일을 순서대로 실행하고 결과를 `data/processed/`에 저장)

## 범위
- **분석 대상 7개 동네**: Westwood(90024), West LA/Sawtelle(90025), Rancho Park(90064), Brentwood(90049), Palms(90034), Mar Vista(90066), Koreatown(90005)
- **비교 기준**: UCLA University Apartments
- 범위 변경 기록: 처음엔 8개 ZIP → 3단계에서 90024·90025 두 곳으로 축소 → 이후 학생들이 실제로 고려하는 동네를 반영해 7곳으로 다시 확대. 이 과정에서 SQL을 "두 지역 비교"에서 "지역 수와 무관하게 동작"하도록 바꿨다(피벗 대신 긴 형태 + 윈도우 함수).

## 핵심 판단 1: 두 출처를 결합한 추정 렌트 (`sql/03`)
- SAFMR은 침실 수 구조는 알려주지만 인접 ZIP을 잘 구분하지 못한다(1BR: Westwood $3,450 vs Sawtelle $3,440).
- ZORI는 ZIP 간 차이를 보여주지만 침실 수 구분이 없다.
- `추정 렌트(zip, 침실) = 최신 ZORI(zip) × SAFMR(zip, 침실) ÷ SAFMR(zip, 1BR)`
- 가정: ZORI ≈ 일반적인 1베드 렌트 (검증 ZIP에서 ZORI ÷ SAFMR 1BR 중앙값 약 1.0).

2BR 추정 렌트 (2026-10): Brentwood $4,859 · Westwood $4,508 · Rancho Park $4,439 · Sawtelle $4,027 · Mar Vista $3,801 · Palms $3,426 · Koreatown $3,050

## 핵심 판단 2: 통학 비용 (`sql/05`)

렌트만 비교하면 "멀수록 싸다"는 결론만 나온다(2베드 4인 1인당 월세: Koreatown $763 vs Westwood $1,127). 그래서 통학 비용을 수단별로 계산했다.

| 수단 | 계산 |
| --- | --- |
| 도보 (Westwood, UCLA 아파트) | 시간만 (9분) |
| 대중교통 | 시간만. 학부생은 Bruin U-Pass로 무료이고, 그 비용은 거주지와 무관하게 모두가 내므로 차이 0 |
| 보유 차량 | UCLA 주차권 (분기 $340.23 → 학기 중 월 $113) + 마일당 $0.29 × 거리 × 왕복 × 16일 + 시간 |
| 새로 산 차량 | 보유 차량 + 보유비 월 $408 (AAA 소형 세단 연 $9,259 − 운행비) |

시간 = 편도 분 × 2 × 16일. 운전은 구글맵 "보통" 범위의 중간값 + 주차·도보 10분.

## 쿼리 목록
| 파일 | 질문 | 핵심 SQL |
| --- | --- | --- |
| `01_load_tables.sql` | 데이터 적재 | `read_csv_auto`, 타입 지정 |
| `02_zori_trend.sql` | 동네별 렌트 추이, 같은 달 Westwood 대비 | `LAG(…, 12)`, `MAX(CASE…) OVER (PARTITION BY month)` |
| `03_market_rent_by_bedroom.sql` | ZIP × 침실 수 추정 렌트 | `QUALIFY ROW_NUMBER()`, 집계 없는 윈도우 |
| `04_per_person_cost.sql` | UCLA vs 같은 구조 외부 아파트 1인당 렌트 | 침실 수 기준 `JOIN`, 파라미터 CTE, `UNION ALL`, `RANK()` |
| `05_commute_cost.sql` | 동네 × 수단별 월 통학 시간·현금 비용 | 스칼라 서브쿼리로 가정값 읽기, `UNION ALL`로 수단 쌓기 |

## 결과: 동네별 통학 (`data/processed/05_commute_cost.csv`)

| 동네 | 대중교통 (분) | 운전 (분, 주차 포함) | 차량 현금 비용 (학기 중 월) |
| --- | --- | --- | --- |
| Westwood | 도보 9 | | |
| Rancho Park | 23 | 26 | $146 |
| Brentwood | 30 | 22.5 | $141 |
| Palms | 31 | 31 | $163 |
| West LA / Sawtelle | 35 | 23.5 | $141 |
| Mar Vista | 42 | 32 | $169 |
| Koreatown | 59 | 67.5 | $201 |

Koreatown은 운전이 대중교통보다 오히려 오래 걸렸다.

## 한계
- 추정 렌트는 "ZORI ≈ 1베드 렌트" 가정에 의존한다(SAFMR 기반 시나리오로 보완, 4단계).
- 통학 시간은 동네별 대표 지점 하나에서 잰 값이다.
- 외부 아파트의 1베드 3인 같은 구성은 현실에서 흔하지 않다. UCLA와 같은 조건 비교를 위해 기계적으로 맞춘 것이다.
