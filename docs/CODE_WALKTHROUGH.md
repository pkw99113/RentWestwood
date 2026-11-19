# 코드 해설: 단계별로 무엇을, 왜, 어떻게 썼나

이 문서는 레포의 코드를 처음부터 끝까지 따라가며 설명한다. 각 절은 **이 코드가 하는 일 → 코드 → 한 줄씩 설명 → 직접 해 보기** 순서다.

## 전체 흐름

```
[원본 데이터]                     [2단계: Python]                 [3~5단계: SQL]                 [5단계: Python]
Zillow ZORI CSV  ──┐
HUD SAFMR XLSX   ──┼─▶ 02_extract_study_area.py ─▶ data/processed/*.csv ─▶ sql/01~10 (03_run_sql.py) ─▶ 05_make_charts.py  → images/
UCLA 요금 (수기) ──┘     (필터, 형태 변환, 품질 점검)     (분석용 테이블)        (DuckDB)                   06_tableau_export.py → data/tableau/
```

**실행 순서** (레포 폴더에서):
```bash
pip install pandas openpyxl duckdb matplotlib
python scripts/02_extract_study_area.py   # 원본 두 파일을 data/raw/에 넣은 뒤
python scripts/03_run_sql.py              # sql/ 폴더의 01~10을 순서대로 실행
python scripts/05_make_charts.py
python scripts/06_tableau_export.py
```

1단계(문제 정의)는 코드가 없으므로 2단계부터 시작한다.

---

## 2단계. 원본 데이터 정리: `scripts/02_extract_study_area.py`

**하는 일**: 전국 데이터(ZORI 8,355개 ZIP, SAFMR 5만여 행)에서 우리 ZIP만 골라, SQL로 다루기 좋은 "긴 형태(long format)" 테이블로 바꾸고, 품질 점검 결과를 문서로 남긴다.

### 2-1. 분석 범위를 한 곳에 정의하기

```python
STUDY_ZIPS = {
    "90024": ("Westwood", "adjacent"),
    "90025": ("West LA / Sawtelle", "near"),
}
VALIDATION_ZIPS = {
    **STUDY_ZIPS,
    "90064": ("Rancho Park", "near"),
    ...
}
```
- 딕셔너리 `{ZIP: (지역 이름, 거리 그룹)}`. 범위를 바꾸고 싶으면 **여기만 고치면** 아래 코드 전체에 반영된다. 3단계에서 8개 ZIP을 2개로 줄일 때도 이 부분만 바꿨다.
- `**STUDY_ZIPS`는 딕셔너리 펼치기. 검증용 목록 = 분석용 2개 + 추가 6개.
- ZIP을 **문자열** `"90024"`로 쓴 이유: 숫자로 쓰면 `02134` 같은 ZIP의 앞자리 0이 사라진다.

### 2-2. 로그를 화면과 문서에 동시에 남기기

```python
report = []
def log(line=""):
    print(line)
    report.append(line)
```
- 점검 결과를 화면에 출력하면서 리스트에도 모아 두고, 마지막에 `docs/02_data_quality_report.md`로 저장한다. **품질 점검 결과가 자동으로 문서가 되는 구조**라, 데이터가 바뀌어도 스크립트만 다시 돌리면 보고서가 갱신된다.

### 2-3. ZORI 읽기: 타입 지정과 앞자리 0 복구

```python
zori = pd.read_csv(RAW / "Zip_zori_uc_sfrcondomfr_sm_month.csv", dtype={"RegionName": str})
zori["RegionName"] = zori["RegionName"].str.zfill(5)
month_cols = [c for c in zori.columns if c[:2] == "20"]
```
- `dtype={"RegionName": str}`: ZIP 컬럼을 문자로 읽는다.
- `.str.zfill(5)`: 5자리가 되도록 앞을 0으로 채운다(`"2134"` → `"02134"`). 원본 파일에서 이미 0이 빠진 경우를 대비한 안전장치.
- `month_cols`: ZORI는 월마다 컬럼이 하나씩 있다(`2015-01-31`, `2015-02-28`, …). 이름이 `"20"`으로 시작하는 컬럼만 골라 월 컬럼 목록을 만든다.

### 2-4. 넓은 형태 → 긴 형태 (`melt`) ⭐

원본 ZORI는 **넓은 형태(wide)**: 한 줄 = 한 ZIP, 컬럼 = 142개 월.

| RegionName | 2015-01-31 | 2015-02-28 | … |
| --- | --- | --- | --- |
| 90024 | 2,231 | 2,261 | … |

SQL로 분석하려면 **긴 형태(long)**가 편하다: 한 줄 = ZIP × 월.

| zip | month | zori |
| --- | --- | --- |
| 90024 | 2015-01 | 2,231 |
| 90024 | 2015-02 | 2,261 |

```python
z = zori[zori["RegionName"].isin(STUDY_ZIPS)]
z_long = z.melt(id_vars="RegionName", value_vars=month_cols, var_name="month", value_name="zori")
z_long = z_long.rename(columns={"RegionName": "zip"})
z_long["month"] = pd.to_datetime(z_long["month"]).dt.to_period("M").astype(str)
```
- `isin(STUDY_ZIPS)`: 딕셔너리에 `isin`을 쓰면 키(ZIP)로 거른다. SQL의 `WHERE zip IN (...)`.
- `melt`: `id_vars`(그대로 둘 컬럼)는 유지하고, `value_vars`(월 컬럼들)를 세로로 쌓는다. 옛 컬럼 이름은 `month`, 값은 `zori` 컬럼이 된다.
- `to_period("M")`: `2015-01-31` → `2015-01`. 월말 날짜는 달마다 다르니(28·30·31일) 월 단위로 통일한다.

**왜 긴 형태인가?** 넓은 형태에서 "ZIP별 전년 대비 상승률"을 구하려면 컬럼 142개를 다뤄야 하지만, 긴 형태에서는 `LAG(zori, 12) OVER (PARTITION BY zip ORDER BY month)` 한 줄이면 된다. **분석용 데이터는 긴 형태, 사람이 보는 표는 넓은 형태**가 기본 원칙이다.

### 2-5. 결측 점검: `groupby`

```python
for k, g in z_long.groupby("zip"):
    ok = g.dropna(subset=["zori"])
    log(f"| {k} | ... | {ok['month'].min()} | {ok['month'].max()} | {len(ok)} | {g['zori'].isna().sum()} |")
```
- `groupby("zip")`를 for문으로 돌리면 `(ZIP, 그 ZIP의 행들)`이 하나씩 나온다.
- 값이 있는 첫 달, 마지막 달, 값 있는 달 수, 빈 달 수를 출력한다. 여기서 "일부 ZIP은 2017년 이전 값이 없다"는 걸 발견했고, 추이 비교 기간을 2018년 이후로 정했다.
- SQL로 쓰면: `SELECT zip, MIN(month), MAX(month), COUNT(zori), SUM(CASE WHEN zori IS NULL THEN 1 ELSE 0 END) FROM ... GROUP BY zip`

### 2-6. SAFMR 읽기: 지저분한 엑셀 헤더 정리

```python
safmr = pd.read_excel(RAW / "fy2026_safmrs_revised.xlsx", dtype={"ZIP\nCode": str})
safmr.columns = [" ".join(str(c).split()) for c in safmr.columns]
```
- HUD 엑셀의 컬럼 이름에는 줄바꿈이 들어 있다(`"SAFMR\n0BR -\n90%\nPayment\nStandard"`).
- `str(c).split()`은 공백·줄바꿈 기준으로 단어를 나누고, `" ".join(...)`으로 다시 공백 하나로 붙인다 → `"SAFMR 0BR - 90% Payment Standard"`. **실무 데이터는 컬럼 이름부터 정리해야 하는 경우가 많다.**

```python
dup = safmr["ZIP Code"].duplicated(keep=False)
```
- `duplicated(keep=False)`: 중복된 값을 **모두** True로 표시한다(기본값은 첫 번째를 빼고 표시). 한 ZIP이 여러 HUD 지역에 걸쳐 있는 경우가 1만 개 넘게 있다는 걸 확인했다. 우리 ZIP은 한 줄씩이라 문제없었다.

### 2-7. SAFMR도 긴 형태로

```python
base_cols = {f"SAFMR {b}BR": b for b in range(5)}
# → {"SAFMR 0BR": 0, "SAFMR 1BR": 1, ..., "SAFMR 4BR": 4}
s_long = s.melt(id_vars="ZIP Code", value_vars=list(base_cols), var_name="col", value_name="safmr")
s_long["bedrooms"] = s_long["col"].map(base_cols)
```
- 딕셔너리 컴프리헨션으로 "컬럼 이름 → 침실 수" 매핑을 만든다.
- 90%·110% 지급 기준 컬럼은 빼고 기본값 5개만 `melt`한다.
- `.map(base_cols)`: `"SAFMR 2BR"` → `2`. 결과는 한 줄 = ZIP × 침실 수.

### 2-8. 두 출처 교차 검증

```python
latest = zori.set_index("RegionName").loc[list(VALIDATION_ZIPS), last_month]
fmr = safmr.set_index("ZIP Code").loc[list(VALIDATION_ZIPS), ["SAFMR 1BR", "SAFMR 2BR"]]
corr = pd.concat([latest, fmr[1]], axis=1).corr().iloc[0, 1]
```
- `set_index(...).loc[ZIP 목록, 컬럼]`: ZIP을 인덱스로 만들어 원하는 ZIP과 컬럼만 꺼낸다.
- `pd.concat(..., axis=1)`: 두 Series를 옆으로 붙인다(인덱스 = ZIP 기준으로 맞춰짐). SQL의 `JOIN ... ON zip`과 같다.
- `.corr()`: 상관계수 행렬. `[0, 1]` 위치가 두 변수의 상관계수(0.93).

### 직접 해 보기
1. `STUDY_ZIPS`에 `"90034"`(Palms)를 추가하고 스크립트를 다시 실행해 보자. 어떤 파일이 바뀌나?
2. `melt`의 반대는 `pivot`이다. `z_long.pivot(index="month", columns="zip", values="zori")`를 실행하고 결과 모양을 보자.

---

## 3단계. SQL로 1인당 비용 만들기

### 3-0. SQL 실행기: `scripts/03_run_sql.py`

```python
con = duckdb.connect()                                   # 메모리 위의 임시 DB
for sql_file in sorted((ROOT / "sql").glob("*.sql")):    # 01, 02, ... 순서대로
    result = con.execute(sql_file.read_text())           # 파일 안의 모든 문장 실행, 마지막 결과 보관
    if result.description is None or result.description[0][0] == "Count":
        continue                                         # 테이블만 만드는 파일은 건너뜀
    df = result.df()
    df.to_csv(OUT / f"{sql_file.stem}.csv", index=False) # 결과를 CSV로 저장
```
- **DuckDB**: 설치만 하면 되는 분석용 DB. 서버가 필요 없고, CSV를 바로 읽으며, BigQuery와 문법이 많이 비슷하다(QUALIFY, 윈도우 함수 등).
- 파일 이름에 번호를 붙여 `sorted`로 실행 순서를 보장한다. 앞 파일이 만든 테이블(예: `market_rent`)을 뒤 파일이 쓴다.
- 각 파일의 마지막 `SELECT` 결과가 `data/processed/파일이름.csv`로 저장된다.

### 3-1. `sql/01_load_tables.sql`: CSV를 테이블로

```sql
CREATE OR REPLACE TABLE zori AS
SELECT CAST(zip AS VARCHAR) AS zip, area, CAST(month || '-01' AS DATE) AS month, zori
FROM read_csv_auto('data/processed/zori_study_zips.csv', types = {'zip': 'VARCHAR'});
```
- `CREATE OR REPLACE TABLE ... AS SELECT`: 조회 결과로 테이블을 만든다(있으면 덮어씀). 다시 실행해도 에러가 안 난다.
- `read_csv_auto`: CSV를 읽고 타입을 자동 추론. 단, ZIP은 숫자로 추론되므로 `types`로 문자 지정.
- `month || '-01'`: `||`는 문자열 이어 붙이기. `'2026-10'` → `'2026-10-01'` → `DATE`로 변환. 날짜 타입이어야 `YEAR()`, 날짜 비교, 정렬이 제대로 된다.

### 3-2. `sql/02_zori_trend.sql`: 전년 대비 상승률과 피벗 ⭐

```sql
WITH yoy AS (
    SELECT zip, month, zori,
           LAG(zori, 12) OVER (PARTITION BY zip ORDER BY month) AS zori_last_year
    FROM zori
),
```
**윈도우 함수 읽는 법**: `함수 OVER (PARTITION BY 그룹 ORDER BY 순서)`
- `PARTITION BY zip`: ZIP별로 따로 계산(그룹을 나누지만 GROUP BY처럼 행을 줄이지 않는다).
- `ORDER BY month`: 그룹 안에서 월 순서로 정렬.
- `LAG(zori, 12)`: 정렬된 순서에서 12행 앞의 값 = 작년 같은 달.

| zip | month | zori | zori_last_year |
| --- | --- | --- | --- |
| 90024 | 2018-01 | 2,825 | 2,628 (2017-01 값) |
| 90024 | 2018-02 | 2,808 | 2,617 (2017-02 값) |

⚠️ LAG는 "12개월 전"이 아니라 "12행 전"이다. 중간에 빠진 달이 있으면 틀리므로, 2단계에서 결측이 없는지 먼저 확인했다.

```sql
wide AS (
    SELECT month,
           MAX(CASE WHEN zip = '90024' THEN zori END) AS westwood,
           MAX(CASE WHEN zip = '90025' THEN zori END) AS west_la,
           ...
    FROM yoy
    GROUP BY month
)
```
**피벗 (긴 형태 → 넓은 형태)**:
- `GROUP BY month`로 한 달에 한 줄을 만든다. 그 달에는 원래 ZIP별 두 줄이 있다.
- `CASE WHEN zip = '90024' THEN zori END`: 90024 행이면 값, 아니면 NULL.
- `MAX(...)`: NULL을 무시하므로 90024의 값만 남는다. (값이 하나뿐이라 MIN, SUM을 써도 결과는 같지만, 관례적으로 MAX를 쓴다.)

```sql
SELECT month,
       ROUND(100 * (westwood / westwood_ly - 1), 1) AS westwood_yoy_pct,
       ROUND(100 * (westwood / west_la - 1), 1)     AS westwood_premium_pct
FROM wide
WHERE month >= DATE '2018-01-01'
ORDER BY month;
```
- 같은 행에 값이 나란히 있으니 나눗셈 한 번으로 상승률과 프리미엄이 나온다.
- `WHERE`는 마지막 SELECT에 걸었다. CTE 안(LAG 계산 전)에서 2018년 이후로 자르면, 2018년의 "작년 값"(2017년)이 사라져 NULL이 된다. **필터를 거는 위치가 결과를 바꾼다.**

### 3-3. `sql/03_market_rent_by_bedroom.sql`: 두 출처 결합 ⭐

```sql
WITH latest_zori AS (
    SELECT zip, zori
    FROM zori
    QUALIFY ROW_NUMBER() OVER (PARTITION BY zip ORDER BY month DESC) = 1
),
```
**그룹별 최신 1개** (쿼리 테스트 단골):
- `ROW_NUMBER() OVER (PARTITION BY zip ORDER BY month DESC)`: ZIP마다 최신 월부터 1, 2, 3… 번호를 매긴다.
- `QUALIFY ... = 1`: 윈도우 함수 결과로 거른다. SQL 실행 순서는 `FROM → WHERE → GROUP BY → HAVING → 윈도우 함수 → QUALIFY → SELECT → ORDER BY`라서 WHERE에서는 윈도우 결과를 쓸 수 없다.
- QUALIFY가 없는 DB(MySQL, PostgreSQL 등)에서는:
  ```sql
  SELECT zip, zori FROM (
      SELECT zip, zori, ROW_NUMBER() OVER (PARTITION BY zip ORDER BY month DESC) AS rn
      FROM zori
  ) t
  WHERE rn = 1;
  ```

```sql
bedroom_ratio AS (
    SELECT zip, bedrooms, safmr,
           safmr / MAX(CASE WHEN bedrooms = 1 THEN safmr END) OVER (PARTITION BY zip) AS ratio_to_1br
    FROM safmr
)
```
- `MAX(CASE WHEN bedrooms = 1 THEN safmr END) OVER (PARTITION BY zip)`: ZIP별 1BR 값을 구해 **그 ZIP의 모든 행 옆에** 붙인다. GROUP BY였다면 ZIP당 한 줄로 줄어들었을 것이다.
- 그래서 각 침실 수의 SAFMR을 같은 ZIP의 1BR로 나눌 수 있다: 0BR 0.89, 2BR 1.25, 3BR 1.58.

```sql
SELECT b.zip, b.bedrooms, b.safmr,
       ROUND(z.zori * b.ratio_to_1br) AS est_market_rent
FROM bedroom_ratio b
JOIN latest_zori z USING (zip)
WHERE b.bedrooms <= 3
```
- `JOIN ... USING (zip)`: 양쪽 컬럼 이름이 같을 때 `ON b.zip = z.zip`의 줄임.
- **추정 렌트 = ZORI(ZIP 수준) × SAFMR 비율(침실 구조)**. Westwood 2BR = $3,617 × 1.246 ≈ $4,508.

### 3-4. `sql/04_per_person_cost.sql`: UCLA vs 외부 ⭐

```sql
WITH params AS (
    SELECT 9 AS ucla_months, 12 AS lease_months, 3 AS summer_months, 0.7 AS sublet_recovery
),
```
- **가정값 테이블**: 한 줄짜리. 숫자를 쿼리 여기저기에 직접 쓰지 않고 이름을 붙여 한 곳에 모은다. 가정을 바꿀 때 여기만 고치면 된다.

```sql
ucla AS (
    SELECT 'UCLA University Apartments' AS option,
           u.unit_type, u.bedrooms, u.occupants, u.bedroom_sharing,
           u.total_contract_usd / p.ucla_months AS school_year_monthly,
           u.total_contract_usd                 AS annual_if_away_in_summer,
           u.total_contract_usd                 AS annual_with_sublet
    FROM ucla_apartments u, params p
),
```
- `FROM 테이블A, 테이블B`: 조건 없이 콤마로 나열하면 모든 조합(CROSS JOIN)이다. params는 1행이라 행 수가 그대로고, 모든 행에 가정값이 붙는다.
- `'UCLA University Apartments' AS option`: 상수 컬럼. 나중에 외부 선택지와 합칠 때 어느 쪽인지 구분하는 라벨.

```sql
off_campus AS (
    SELECT CASE m.zip WHEN '90024' THEN 'Westwood (90024)' ELSE 'West LA (90025)' END AS option,
           ...
           m.est_market_rent / u.occupants AS school_year_monthly,
           m.est_market_rent / u.occupants * p.lease_months AS annual_if_away_in_summer,
           m.est_market_rent / u.occupants * (p.lease_months - p.summer_months * p.sublet_recovery) AS annual_with_sublet
    FROM ucla_apartments u
    JOIN market_rent m ON m.bedrooms = u.bedrooms
    CROSS JOIN params p
)
```
- `JOIN market_rent m ON m.bedrooms = u.bedrooms`: UCLA 유형마다 **같은 침실 수**의 외부 렌트를 붙인다. market_rent에는 침실 수마다 ZIP이 2개 → UCLA 1행이 2행(Westwood, West LA)이 된다. **JOIN 결과 행 수 = 8 × 2 = 16을 미리 예상**하고 확인한다.
- `/ u.occupants`: UCLA와 같은 인원으로 나눠야 공정한 비교.
- 서브렛 공식: `12 - 3 × 0.7 = 9.9`개월치를 실제로 부담 = 여름 3개월 중 70%를 돌려받음.
- `CASE m.zip WHEN '90024' THEN ... ELSE ... END`: 단순 CASE 문법. `CASE WHEN m.zip = '90024' THEN ...`과 같다.

```sql
SELECT * FROM ucla
UNION ALL
SELECT * FROM off_campus;
```
- 컬럼 개수·순서·타입이 같은 두 결과를 **위아래로** 붙인다. JOIN은 옆으로, UNION은 아래로.
- `UNION`(중복 제거)이 아니라 `UNION ALL`: 두 쪽은 겹칠 수 없고, 중복 제거는 비용도 들고 우연히 같은 행을 지울 위험도 있다.

```sql
RANK() OVER (PARTITION BY unit_type ORDER BY annual_if_away_in_summer) AS rank_annual_if_away
```
- 같은 유형 안에서 비용이 싼 순서로 순위. 동점이면 같은 순위.
- `ROW_NUMBER`(1,2,3 무조건) vs `RANK`(1,1,3) vs `DENSE_RANK`(1,1,2) 차이를 기억하자.

### 3-5. `sql/05_commute_breakeven.sql`: 손익분기

```sql
SELECT unit_type, occupants,
       ROUND(westwood - west_la) AS monthly_savings_west_la,
       ROUND(p.extra_minutes_one_way * 2 * p.campus_days_per_month / 60.0, 1) AS extra_hours_per_month,
       ROUND((westwood - west_la) / (p.extra_minutes_one_way * 2 * p.campus_days_per_month / 60.0), 2) AS breakeven_usd_per_hour
FROM pivoted, params p
```
- 04 결과를 피벗(3-2와 같은 `MAX(CASE WHEN)` 패턴)해서 두 지역을 한 행에 놓고 계산한다.
- `/ 60.0`: **정수 나눗셈 함정** 대비. DuckDB와 BigQuery는 `/`가 항상 소수 나눗셈이지만, PostgreSQL이나 SQL Server에서는 정수끼리 나누면 소수점이 잘린다(`470 / 60` = 7). `60.0`으로 쓰면 어느 DB에서든 소수 계산이 된다. 쿼리 테스트에서 비율을 계산할 때 자주 틀리는 부분이다.

### 직접 해 보기
1. `04`의 params에서 `sublet_recovery`를 0.5로 바꾸고 다시 실행해 보자. 2/4 apartment의 순위가 바뀌나?
2. `03`의 `latest_zori`를 QUALIFY 없이 서브쿼리 방식으로 다시 써 보자.
3. `02`에서 `PARTITION BY zip`을 지우면 어떤 행의 값이 틀어지는지 확인해 보자.

---

## 4단계. 민감도 분석

### 4-1. `sql/06_sensitivity.sql`: 시나리오 조합 만들기 ⭐

```sql
WITH rent_method(rent_method) AS (
    VALUES ('zori_adjusted'), ('safmr'), ('safmr_110')
),
summer_plan(summer_plan, sublet_recovery, ucla_needs_summer_housing) AS (
    VALUES ('away', 0.0, FALSE), ('sublet_50', 0.5, FALSE), ('sublet_70', 0.7, FALSE),
           ('sublet_90', 0.9, FALSE), ('stay_in_la', 0.0, TRUE)
),
```
- `VALUES (...), (...)`: 테이블 없이 쿼리 안에서 작은 표를 직접 만든다. `이름(컬럼1, 컬럼2)`로 컬럼 이름을 붙인다.
- 시나리오 목록을 데이터처럼 다루면, 시나리오를 추가할 때 한 줄만 넣으면 된다.

```sql
rent AS (
    SELECT m.zip, m.bedrooms, r.rent_method,
           CASE r.rent_method
               WHEN 'zori_adjusted' THEN m.est_market_rent
               WHEN 'safmr'         THEN m.safmr
               WHEN 'safmr_110'     THEN m.safmr * 1.10
           END AS unit_rent
    FROM market_rent m
    CROSS JOIN rent_method r
),
```
- `CROSS JOIN`: 모든 조합. market_rent 8행 × 방법 3개 = 24행. **민감도 분석의 핵심 도구**다.
- CASE로 방법마다 다른 렌트 값을 고른다.

```sql
scenarios AS (
    SELECT ... 'Westwood' or 'West LA' AS option,
           p.pp_monthly * (12 - 3 * s.sublet_recovery) AS annual_cost
    FROM pp p CROSS JOIN summer_plan s
    UNION ALL
    SELECT ... 'UCLA' AS option,
           p.total_contract_usd + CASE WHEN s.ucla_needs_summer_housing THEN 3 * p.pp_monthly ELSE 0 END AS annual_cost
    FROM pp p CROSS JOIN summer_plan s
    WHERE p.zip = '90025'
)
```
- 외부: 1인당 월세 × (12 − 서브렛으로 돌려받는 개월 수).
- UCLA: 계약 총액 + (LA에 남으면 여름 3개월 숙소비).
- ⚠️ `WHERE p.zip = '90025'`: pp 테이블은 유형마다 ZIP 2개라 UCLA 행이 두 번 생긴다. **JOIN 팽창**을 막으려고 하나만 남겼다(UCLA 요금은 ZIP과 무관). 이 줄이 없으면 UCLA가 같은 시나리오에 두 번 나와 순위가 꼬인다.

### 4-2. `sql/07_win_share.sql`: 승률과 차이 크기

```sql
WITH ranked AS (
    SELECT *,
           LEAD(annual_cost) OVER (PARTITION BY unit_type, rent_method, summer_plan ORDER BY annual_cost) AS runner_up_cost
    FROM sensitivity
)
SELECT summer_plan, option AS winner,
       COUNT(*) AS scenarios_won,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY summer_plan), 0) AS share_pct,
       ROUND(MEDIAN(runner_up_cost - annual_cost)) AS median_margin_usd
FROM ranked
WHERE cost_rank = 1
GROUP BY summer_plan, option
```
- `LEAD`: LAG의 반대로, 다음 행의 값. 비용순으로 정렬했으니 1등 행의 LEAD = 2등의 비용 → `차이 = 2등 − 1등`.
- `SUM(COUNT(*)) OVER (PARTITION BY summer_plan)`: **집계 위에 윈도우 함수**. GROUP BY가 먼저 실행돼 `COUNT(*)`(선택지별 승리 수)가 나오고, 그 결과 위에서 여름 계획별 합계(24)를 구한다. 비율 = 승리 수 ÷ 합계. GA4 프로젝트 7단계에서 쓴 패턴과 같다.
- `MEDIAN`: 중앙값. 평균보다 극단값에 덜 흔들린다.

### 4-3. `sql/08_recommendation.sql`: 결론이 견고한가

```sql
SELECT unit_type, summer_plan,
       COUNT(DISTINCT option) AS n_distinct_winners,
       MODE(option)           AS most_common_winner,
       STRING_AGG(rent_method || '=' || option, ', ' ORDER BY rent_method) AS detail
FROM winners
GROUP BY unit_type, summer_plan
```
- `COUNT(DISTINCT option) = 1`이면 세 렌트 추정 방식에서 모두 같은 선택이 이겼다는 뜻 → "robust".
- `MODE()`: 가장 자주 나온 값(최빈값).
- `STRING_AGG(값, 구분자)`: 그룹 안의 값들을 문자열 하나로 이어 붙인다. BigQuery에도 같은 이름, MySQL은 `GROUP_CONCAT`.

```sql
ORDER BY unit_type,
         CASE summer_plan WHEN 'away' THEN 1 WHEN 'sublet_50' THEN 2 ... ELSE 5 END;
```
- **사용자 정의 정렬**: 알파벳순이 아니라 원하는 순서로 정렬할 때 CASE로 번호를 매긴다.

### 직접 해 보기
1. `06`의 summer_plan에 `('sublet_30', 0.3, FALSE)`를 추가해 보자. 07, 08 결과가 어떻게 바뀌나?
2. `06`에서 `WHERE p.zip = '90025'`를 지우고 실행한 뒤, UCLA 행이 몇 개가 되는지 세어 보자.

---

## 5단계. 추이, 차트, 내보내기

### 5-1. `sql/09_trend_summary.sql`: 연도별 요약

```sql
yearly AS (
    SELECT zip, YEAR(month) AS year, AVG(zori) AS avg_rent, COUNT(*) AS months
    FROM zori WHERE month >= DATE '2018-01-01'
    GROUP BY zip, YEAR(month)
)
...
ROUND(100 * (westwood / LAG(westwood) OVER (ORDER BY year) - 1), 1)   AS westwood_growth_pct,
ROUND(100 * westwood / FIRST_VALUE(westwood) OVER (ORDER BY year), 1) AS westwood_index_2018
```
- `COUNT(*) AS months`: 2026년은 10개월뿐이라 불완전한 해임을 표시. 연평균을 비교할 때 이런 표시가 없으면 오해가 생긴다.
- 연도당 한 줄이라 `LAG(...)`(오프셋 생략 = 1)가 곧 전년 값.
- `FIRST_VALUE`: 정렬 순서의 첫 값 = 2018년. 매년 값을 2018년으로 나누면 **지수(2018 = 100)**가 된다. 출발점이 다른 두 지역의 상승 속도를 비교할 때 쓴다.

### 5-2. `sql/10_premium_seasonality.sql`: 추세를 빼고 계절성만 보기

```sql
deviation AS (
    SELECT month,
           premium_pct - AVG(premium_pct) OVER (PARTITION BY YEAR(month)) AS gap_vs_year_avg
    FROM monthly
)
SELECT MONTH(month) AS calendar_month,
       ROUND(AVG(gap_vs_year_avg), 2) AS avg_gap_pctpt,
       SUM(CASE WHEN gap_vs_year_avg > 0 THEN 1 ELSE 0 END) AS years_above_avg
FROM deviation
GROUP BY MONTH(month)
```
- 프리미엄이 해마다 오르고 있어서, 월별 값을 그냥 평균 내면 추세가 섞인다.
- `AVG(...) OVER (PARTITION BY YEAR(month))`: 각 달 옆에 그해 평균을 붙이고 빼서 "그해 평균보다 얼마나 높은가"만 남긴다.
- 그다음 같은 달(1월끼리, 5월끼리)로 묶어 평균 낸다. `years_above_avg`는 "9년 중 몇 해나 평균보다 높았나"로, 평균 하나보다 패턴이 일관적인지를 보여준다.

### 5-3. `scripts/05_make_charts.py`: 차트

```python
COLOR = {"Westwood": "#2a78d6", "West LA": "#eb6834", "UCLA": "#1baf7a"}
```
- **선택지별 색을 고정**해서 모든 차트에서 같은 대상은 같은 색이다.

```python
fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 6.2), sharex=True,
                             gridspec_kw={"height_ratios": [2.2, 1], "hspace": 0.12})
```
- 차트 두 개를 위아래로 만들고 x축(날짜)을 공유한다. 렌트($)와 프리미엄(%)은 단위가 달라서 **한 차트에 축 두 개를 쓰지 않고** 나눴다.

```python
a1.annotate(f"{name}  ${last[col]:,.0f}", (last["month"], last[col]), xytext=(6, 0),
            textcoords="offset points", va="center")
```
- 범례 대신 선 끝에 이름과 최신 값을 직접 단다(direct label). 읽는 사람이 색과 범례를 오가지 않아도 된다.

```python
xs = [j + (i - 1) * (w + gap) for j in range(len(plans))]
ax.bar(xs, vals, width=w, color=COLOR[o], label=o)
```
- 묶음 막대: 여름 계획(j)마다 선택지(i = 0, 1, 2)를 왼쪽·가운데·오른쪽으로 조금씩 밀어서 그린다.

### 5-4. `scripts/06_tableau_export.py`: 대시보드용 데이터

```python
trend = z.melt(id_vars=["month", "westwood_premium_pct"], value_vars=["westwood_rent", "west_la_rent"],
               var_name="area", value_name="rent")
s = s.merge(occ, on="unit_type", how="left")
s["is_cheapest"] = (s["cost_rank"] == 1).astype(int)
```
- Tableau도 긴 형태를 좋아한다: `area`를 색상에 넣으면 선이 자동으로 나뉜다. 그래서 피벗했던 결과를 다시 `melt`로 길게 만든다.
- `merge(..., how="left")`: SQL의 LEFT JOIN. 시나리오 표에 인원 수를 붙인다.
- `is_cheapest`를 0/1 플래그로 만들면 Tableau에서 `SUM`은 승리 횟수, `AVG`는 승률이 된다. GA4 프로젝트의 0/1 플래그와 같은 아이디어다.

---

## 이 프로젝트에서 쓴 SQL 패턴 모음 (쿼리 테스트 대비)

| 패턴 | 쓴 곳 | 한 줄 요약 |
| --- | --- | --- |
| `LAG / LEAD` | 02, 07, 09 | 앞·뒤 행 값 가져오기 (전년 대비, 1등과 2등 차이) |
| `MAX(CASE WHEN …)` 피벗 | 02, 05, 06, 09, 10 | 긴 형태 → 넓은 형태 |
| `ROW_NUMBER` + `QUALIFY` | 03 | 그룹별 최신·최고 1개 |
| 집계 없는 윈도우 (`MAX(...) OVER`) | 03, 10 | 그룹 값을 모든 행 옆에 붙이기 |
| `CROSS JOIN` + `VALUES` | 06 | 시나리오 조합 만들기 |
| 파라미터 CTE | 04, 05 | 가정값을 한 곳에 모으기 |
| `UNION ALL` | 04, 06 | 구조가 같은 결과를 아래로 합치기 |
| `RANK` | 04, 06 | 동점 허용 순위 |
| `SUM(COUNT(*)) OVER` | 07 | 집계 결과 위에서 비율 계산 |
| `COUNT(DISTINCT) = 1` | 08 | 모든 조건에서 결과가 같은지 확인 |
| `FIRST_VALUE` | 09 | 기준 시점 대비 지수 |
| `CASE` 정렬 | 08 | 원하는 순서로 정렬 |
