# 코드 해설: 단계별로 무엇을, 왜, 어떻게 썼나

이 문서는 레포의 코드를 처음부터 끝까지 따라가며 설명한다. 각 절은 **이 코드가 하는 일 → 코드 → 한 줄씩 설명 → 직접 해 보기** 순서다.

## 전체 흐름

```
[원본 데이터]                     [2단계: Python]                 [3~5단계: SQL]                 [5단계: Python]
Zillow ZORI CSV  ──┐
HUD SAFMR XLSX   ──┼─▶ 02_extract_study_area.py ─▶ data/processed/*.csv ─▶ sql/01~11 (03_run_sql.py) ─▶ 05_make_charts.py  → images/
UCLA 요금·구글맵 통학·비용 가정 (수기) ──┘     (필터, 형태 변환, 품질 점검)     (분석용 테이블)        (DuckDB)                   06_tableau_export.py → data/tableau/
```

**실행 순서** (레포 폴더에서):
```bash
pip install pandas openpyxl duckdb matplotlib
python scripts/02_extract_study_area.py   # 원본 두 파일을 data/raw/에 넣은 뒤
python scripts/03_run_sql.py              # sql/ 폴더의 01~11을 순서대로 실행
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
    "90064": ("Rancho Park", "near"),
    ...
    "90005": ("Koreatown", "far"),
}
VALIDATION_ZIPS = {
    **STUDY_ZIPS,
    "90020": ("Koreatown (90020)", "far"),
}
```
- 딕셔너리 `{ZIP: (지역 이름, 거리 그룹)}`. 범위를 바꾸고 싶으면 **여기만 고치면** 아래 코드 전체에 반영된다. 범위를 8개 → 2개 → 7개로 바꿀 때마다 이 부분만 고쳤다.
- `**STUDY_ZIPS`는 딕셔너리 펼치기. 검증용 목록 = 분석용 7개 + ZORI 이상치인 90020.
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


## 3단계. SQL로 1인당 비용과 통학 비용 만들기

### 3-0. SQL 실행기: `scripts/03_run_sql.py`

```python
con = duckdb.connect()                                   # 메모리 위의 임시 DB
for sql_file in sorted((ROOT / "sql").glob("*.sql")):    # 01, 02, ... 순서대로
    result = con.execute(sql_file.read_text())           # 파일 안의 모든 문장 실행, 마지막 결과 보관
    if result.description is None or result.description[0][0] == "Count":
        continue                                         # 테이블만 만드는 파일은 건너뜀
    df = result.df()
    df.to_csv(OUT / f"{sql_file.stem}.csv", index=False) # 결과를 CSV로 저장
...
con.execute("SELECT * FROM sensitivity ...").df().to_csv(OUT / "sensitivity_full.csv", index=False)
```
- **DuckDB**: 설치만 하면 되는 분석용 DB. 서버가 필요 없고, CSV를 바로 읽으며, BigQuery와 문법이 많이 비슷하다(QUALIFY, 윈도우 함수 등).
- 파일 이름에 번호를 붙여 `sorted`로 실행 순서를 보장한다. 앞 파일이 만든 테이블(예: `market_rent`, `commute_cost`)을 뒤 파일이 쓴다.
- 각 파일의 마지막 `SELECT` 결과가 `data/processed/파일이름.csv`로 저장된다. 시나리오 전체 표는 마지막에 따로 저장한다(차트·Tableau용).

### 3-1. `sql/01_load_tables.sql`: CSV를 테이블로

```sql
CREATE OR REPLACE TABLE zori AS
SELECT CAST(zip AS VARCHAR) AS zip, area, distance_group, CAST(month || '-01' AS DATE) AS month, zori
FROM read_csv_auto('data/processed/zori_study_zips.csv', types = {'zip': 'VARCHAR'});
...
CREATE OR REPLACE TABLE commute_times AS
SELECT CAST(zip AS VARCHAR) AS zip, area, transit_min, walk_min,
       (drive_min_low + drive_min_high) / 2.0 AS drive_min_mid,
       drive_miles
FROM read_csv_auto('data/raw/commute_times_google_maps.csv', types = {'zip': 'VARCHAR'});
```
- `CREATE OR REPLACE TABLE ... AS SELECT`: 조회 결과로 테이블을 만든다(있으면 덮어씀). 다시 실행해도 에러가 안 난다.
- `read_csv_auto`: CSV를 읽고 타입을 자동 추론. 단, ZIP은 숫자로 추론되므로 `types`로 문자 지정.
- `month || '-01'`: `||`는 문자열 이어 붙이기. `'2026-10'` → `'2026-10-01'` → `DATE`. 날짜 타입이어야 `YEAR()`, 날짜 비교, 정렬이 제대로 된다.
- `(low + high) / 2.0`: 구글맵의 "보통 35~80분"을 중간값 하나로 바꾼다. 적재 단계에서 파생 컬럼을 만들어 두면 뒤 쿼리가 단순해진다.

### 3-2. `sql/02_zori_trend.sql`: 전년 대비, 그리고 "같은 달 Westwood 대비" ⭐

```sql
WITH base AS (
    SELECT zip, area, month, zori,
           LAG(zori, 12) OVER (PARTITION BY zip ORDER BY month)                AS zori_last_year,
           MAX(CASE WHEN zip = '90024' THEN zori END) OVER (PARTITION BY month) AS westwood_same_month
    FROM zori
)
SELECT zip, area, month,
       ROUND(100 * (zori / zori_last_year - 1), 1)      AS yoy_pct,
       ROUND(100 * (zori / westwood_same_month - 1), 1) AS pct_vs_westwood
FROM base
WHERE month >= DATE '2018-01-01'
ORDER BY zip, month;
```
**윈도우 함수 읽는 법**: `함수 OVER (PARTITION BY 그룹 ORDER BY 순서)`
- `LAG(zori, 12) OVER (PARTITION BY zip ORDER BY month)`: ZIP별로, 월 순서로 정렬했을 때 12행 앞의 값 = 작년 같은 달.

| zip | month | zori | zori_last_year |
| --- | --- | --- | --- |
| 90024 | 2018-01 | 2,825 | 2,628 (2017-01 값) |
| 90024 | 2018-02 | 2,808 | 2,617 (2017-02 값) |

- `MAX(CASE WHEN zip = '90024' THEN zori END) OVER (PARTITION BY month)`: **같은 달의 모든 행**(7개 ZIP)에 그 달 Westwood 값을 붙인다. 행을 줄이지 않으니 각 동네가 Westwood보다 몇 % 싼지 바로 나눌 수 있다.
- ⚠️ LAG는 "12개월 전"이 아니라 "12행 전"이다. 빠진 달이 있으면 틀리므로, 2단계에서 결측이 없는지 먼저 확인했다.
- ⚠️ `WHERE`는 마지막 SELECT에 걸었다. CTE 안(LAG 계산 전)에서 2018년 이후로 자르면 2018년의 "작년 값"(2017년)이 사라진다. **필터를 거는 위치가 결과를 바꾼다.**

**설계 변경 이야기**: 지역이 두 곳일 때는 `MAX(CASE WHEN …) … GROUP BY month`로 피벗해 `westwood`, `west_la` 컬럼을 만들었다. 그런데 지역이 7곳이 되자 컬럼을 7개 써야 했다. 그래서 **긴 형태를 유지하고 기준값(Westwood)만 윈도우로 붙이는 방식**으로 바꿨다. 지역 수가 바뀌어도 쿼리를 고칠 필요가 없다.

### 3-3. `sql/03_market_rent_by_bedroom.sql`: 두 출처 결합 ⭐

```sql
WITH latest_zori AS (
    SELECT zip, zori
    FROM zori
    QUALIFY ROW_NUMBER() OVER (PARTITION BY zip ORDER BY month DESC) = 1
),
bedroom_ratio AS (
    SELECT zip, area, distance_group, bedrooms, safmr,
           safmr / MAX(CASE WHEN bedrooms = 1 THEN safmr END) OVER (PARTITION BY zip) AS ratio_to_1br
    FROM safmr
)
SELECT b.zip, b.area, b.bedrooms, b.safmr, ROUND(z.zori * b.ratio_to_1br) AS est_market_rent
FROM bedroom_ratio b
JOIN latest_zori z USING (zip)
WHERE b.bedrooms <= 3
```
**그룹별 최신 1개** (쿼리 테스트 단골):
- `ROW_NUMBER() OVER (PARTITION BY zip ORDER BY month DESC)`: ZIP마다 최신 월부터 1, 2, 3… 번호.
- `QUALIFY ... = 1`: 윈도우 함수 결과로 거른다. 실행 순서가 `FROM → WHERE → GROUP BY → HAVING → 윈도우 → QUALIFY → SELECT → ORDER BY`라서 WHERE에서는 윈도우 결과를 쓸 수 없다.
- QUALIFY가 없는 DB에서는:
  ```sql
  SELECT zip, zori FROM (
      SELECT zip, zori, ROW_NUMBER() OVER (PARTITION BY zip ORDER BY month DESC) AS rn
      FROM zori
  ) t
  WHERE rn = 1;
  ```

**집계 없는 윈도우**: `MAX(CASE WHEN bedrooms = 1 THEN safmr END) OVER (PARTITION BY zip)`는 ZIP별 1BR 값을 그 ZIP의 모든 행 옆에 붙인다. GROUP BY였다면 ZIP당 한 줄로 줄었을 것이다. 그래서 각 침실 수를 1BR로 나눌 수 있다(0BR 0.89, 2BR 1.25, 3BR 1.58).

`JOIN ... USING (zip)`은 컬럼 이름이 같을 때 `ON b.zip = z.zip`의 줄임. **추정 렌트 = ZORI(ZIP 수준) × SAFMR 비율(침실 구조)**. 예: Westwood 2BR = $3,617 × 1.246 ≈ $4,508.

### 3-4. `sql/04_per_person_cost.sql`: UCLA vs 외부 렌트 ⭐

```sql
WITH params AS (
    SELECT 9 AS ucla_months, 12 AS lease_months, 3 AS summer_months, 0.7 AS sublet_recovery
),
ucla AS (
    SELECT 'UCLA' AS option, NULL AS zip, u.unit_type, u.bedrooms, u.occupants,
           u.total_contract_usd / p.ucla_months AS school_year_monthly,
           u.total_contract_usd                 AS annual_if_away_in_summer, ...
    FROM ucla_apartments u, params p
),
off_campus AS (
    SELECT m.area AS option, m.zip, u.unit_type, u.bedrooms, u.occupants,
           m.est_market_rent / u.occupants AS school_year_monthly,
           m.est_market_rent / u.occupants * p.lease_months AS annual_if_away_in_summer,
           m.est_market_rent / u.occupants * (p.lease_months - p.summer_months * p.sublet_recovery) AS annual_with_sublet
    FROM ucla_apartments u
    JOIN market_rent m ON m.bedrooms = u.bedrooms
    CROSS JOIN params p
)
SELECT * FROM ucla
UNION ALL
SELECT * FROM off_campus;
```
- **params CTE**: 가정값을 한 줄짜리 테이블에 모은다. `FROM 테이블, params`(콤마 = CROSS JOIN)로 붙여도 1행이라 행 수는 그대로.
- `JOIN market_rent m ON m.bedrooms = u.bedrooms`: UCLA 유형마다 **같은 침실 수**의 외부 렌트를 붙인다. market_rent에는 침실 수마다 동네가 7개 → UCLA 1행이 7행이 된다. **JOIN 결과 행 수(8 × 7 = 56)를 미리 예상**하고 확인한다.
- `NULL AS zip`: UNION ALL은 양쪽 컬럼 개수와 순서가 같아야 해서, UCLA 쪽에 없는 ZIP을 NULL로 채운다.
- `/ u.occupants`: UCLA와 같은 인원으로 나눠야 공정한 비교. 서브렛 공식 `12 − 3 × 0.7 = 9.9`개월치 부담.
- `UNION`(중복 제거) 대신 `UNION ALL`: 두 쪽은 겹칠 수 없고, 중복 제거는 비용도 들고 우연히 같은 행을 지울 위험도 있다.
- 마지막 SELECT의 `RANK() OVER (PARTITION BY unit_type ORDER BY …)`: 같은 유형 안에서 싼 순서. `ROW_NUMBER`(1,2,3) vs `RANK`(1,1,3) vs `DENSE_RANK`(1,1,2).

### 3-5. `sql/05_commute_cost.sql`: 통학 수단별 비용 ⭐

```sql
WITH params AS (
    SELECT
        16 AS campus_days_per_month,
        10 AS park_walk_min,
        (SELECT value FROM cost_assumptions WHERE item = 'ucla_commuter_parking_permit') * 3 / 9.0
            AS parking_per_school_month,
        (SELECT SUM(value) FROM cost_assumptions
          WHERE item IN ('car_fuel_cost', 'car_maintenance_repair_tires')) AS car_cost_per_mile,
        ...
),
modes AS (
    SELECT zip, 'walk' AS mode, walk_min AS one_way_min, 0.0 AS cash_per_school_month, 0.0 AS fixed_per_month
    FROM commute_times WHERE walk_min IS NOT NULL
    UNION ALL
    SELECT zip, 'transit', transit_min, 0.0, 0.0
    FROM commute_times WHERE transit_min IS NOT NULL
    UNION ALL
    SELECT c.zip, 'car_owned', c.drive_min_mid + p.park_walk_min,
           p.parking_per_school_month + c.drive_miles * 2 * p.campus_days_per_month * p.car_cost_per_mile,
           0.0
    FROM commute_times c, params p WHERE c.drive_miles IS NOT NULL
    UNION ALL
    SELECT ... 'car_bought' ... p.car_fixed_per_month ...
)
SELECT m.zip, t.area, m.mode, m.one_way_min,
       ROUND(m.one_way_min * 2 * p.campus_days_per_month / 60.0, 1) AS hours_per_school_month, ...
```
- **스칼라 서브쿼리** `(SELECT value FROM … WHERE item = …)`: 값 하나를 돌려주는 서브쿼리는 숫자처럼 쓸 수 있다. 가정값을 CSV에 출처와 함께 두고, 쿼리는 이름으로 읽어 온다. 주차비가 바뀌면 CSV만 고치면 된다.
- **수단을 UNION ALL로 쌓기**: 수단마다 계산식이 달라서, 수단별 SELECT를 따로 쓰고 위아래로 붙였다. 결과는 "동네 × 수단" 긴 형태라 뒤 쿼리에서 원하는 수단만 고르기 쉽다.
- `WHERE walk_min IS NOT NULL`: 도보는 Westwood에만 값이 있다. NULL 처리로 "가능한 수단만" 행을 만든다.
- `/ 60.0`, `/ 9.0`: **정수 나눗셈 함정** 대비. DuckDB·BigQuery는 `/`가 소수 나눗셈이지만 PostgreSQL·SQL Server는 정수끼리 나누면 소수점이 잘린다(`470 / 60` = 7). 쿼리 테스트에서 비율 계산할 때 자주 틀린다.

### 직접 해 보기
1. `05`의 params에서 `park_walk_min`을 0으로 바꾸면 Koreatown의 운전이 대중교통보다 빨라지나?
2. `03`의 `latest_zori`를 QUALIFY 없이 서브쿼리 방식으로 다시 써 보자.
3. `02`에서 `PARTITION BY zip`을 지우면 어떤 행의 값이 틀어지는지 확인해 보자.

---

## 4단계. 민감도 분석

### 4-1. `sql/06_sensitivity.sql`: 1,080개 시나리오 ⭐

**① 시나리오 목록을 VALUES로 만들기**
```sql
WITH rent_method(rent_method) AS (VALUES ('zori_adjusted'), ('safmr'), ('safmr_110')),
summer_plan(summer_plan, sublet_recovery, ucla_needs_summer_housing) AS (
    VALUES ('away', 0.0, FALSE), ('sublet_50', 0.5, FALSE), ..., ('stay_in_la', 0.0, TRUE)
),
car_profile(car_profile) AS (VALUES ('transit'), ('drives_owned'), ('drives_bought')),
time_value(time_value)   AS (VALUES (0.0), (20.0), (35.0)),
```
- `VALUES`로 쿼리 안에서 작은 표를 만든다. 시나리오를 데이터처럼 다루면, 추가할 때 한 줄만 넣으면 된다.

**② CROSS JOIN으로 모든 조합**
```sql
rent AS (
    SELECT m.zip, m.area, m.bedrooms, r.rent_method,
           CASE r.rent_method WHEN 'zori_adjusted' THEN m.est_market_rent
                              WHEN 'safmr' THEN m.safmr
                              WHEN 'safmr_110' THEN m.safmr * 1.10 END AS unit_rent
    FROM market_rent m CROSS JOIN rent_method r
),
commute_annual AS (
    SELECT c.zip, c.mode, t.time_value,
           9 * (c.cash_per_school_month + c.hours_per_school_month * t.time_value) + 12 * c.fixed_per_month
             AS annual_commute_cost
    FROM commute_cost c CROSS JOIN time_value t
),
```
- `CROSS JOIN` = 모든 조합. 렌트 28행 × 방법 3 = 84행, 통학 19행 × 시간 가치 3 = 57행.
- 통학은 학기 중 9개월만, 차량 보유비는 12개월 내내 든다.

**③ 프로필별로 쓸 수 있는 수단만 고르기**
```sql
best_commute AS (
    SELECT a.zip, p.car_profile, a.time_value, MIN(a.annual_commute_cost) AS annual_commute_cost
    FROM commute_annual a
    CROSS JOIN car_profile p
    WHERE a.mode = 'walk'
       OR (p.car_profile = 'transit'       AND a.mode = 'transit')
       OR (p.car_profile = 'drives_owned'  AND a.mode = 'car_owned')
       OR (p.car_profile = 'drives_bought' AND a.mode = 'car_bought')
    GROUP BY a.zip, p.car_profile, a.time_value
),
```
- `WHERE ... OR (...)`: "도보가 가능하면 도보, 아니면 그 프로필의 수단"이라는 규칙을 조건 하나로 쓴다. Westwood는 도보와 프로필 수단이 둘 다 남을 수 있어서 `MIN`으로 싼 쪽을 고른다.
- ⚠️ `AND`와 `OR`가 섞이면 괄호가 필수다. `AND`가 먼저 계산되기 때문이다.

**④ UCLA 행이 중복되지 않게**
```sql
SELECT p.unit_type, p.rent_method, s.summer_plan, uc.car_profile, uc.time_value,
       'UCLA' AS option,
       MIN(p.total_contract_usd)
         + CASE WHEN s.ucla_needs_summer_housing THEN 3 * MIN(p.pp_monthly) ELSE 0 END AS annual_rent, ...
FROM pp p CROSS JOIN summer_plan s CROSS JOIN ucla_commute uc
GROUP BY p.unit_type, p.rent_method, s.summer_plan, s.ucla_needs_summer_housing, uc.car_profile, uc.time_value
```
- `pp`에는 유형마다 동네 7행이 있어서, 그대로 쓰면 UCLA가 같은 시나리오에 7번 나온다(**JOIN 팽창**).
- GROUP BY로 시나리오당 한 줄로 접는다. UCLA 요금은 동네와 무관하니 `MIN`(어느 행이든 같은 값)으로 꺼낸다. LA에 남는 경우의 여름 숙소비는 `MIN(p.pp_monthly)` = 가장 싼 동네 렌트.
- 처음 두 지역 버전에서는 `WHERE p.zip = '90025'`로 한 행만 남겼는데, 지역이 바뀌어도 깨지지 않도록 GROUP BY 방식으로 바꿨다.

**⑤ 순위**
```sql
RANK() OVER (PARTITION BY unit_type, rent_method, summer_plan, car_profile, time_value
             ORDER BY annual_rent + annual_commute_cost) AS cost_rank
```
- PARTITION BY에 시나리오를 구성하는 다섯 차원을 모두 넣어야 "같은 시나리오 안에서의 순위"가 된다. 하나라도 빠지면 다른 시나리오끼리 순위를 매기게 된다.

### 4-2. `sql/07_win_share.sql`: 승률과 차이 크기

```sql
WITH ranked AS (
    SELECT *, LEAD(annual_cost) OVER (PARTITION BY unit_type, rent_method, summer_plan, car_profile, time_value
                                      ORDER BY annual_cost) AS runner_up_cost
    FROM sensitivity
)
SELECT car_profile, summer_plan, option AS winner,
       COUNT(*) AS scenarios_won,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY car_profile, summer_plan), 0) AS share_pct,
       ROUND(MEDIAN(runner_up_cost - annual_cost)) AS median_margin_usd
FROM ranked WHERE cost_rank = 1
GROUP BY car_profile, summer_plan, option
```
- `LEAD`: 다음 행 값. 비용순 정렬에서 1등 행의 LEAD = 2등 비용 → 차이 = 2등 − 1등.
- `SUM(COUNT(*)) OVER (...)`: **집계 위에 윈도우**. GROUP BY가 먼저 실행돼 선택지별 승리 수가 나오고, 그 위에서 그룹 합계를 구해 비율을 낸다. GA4 프로젝트 7단계와 같은 패턴.
- `MEDIAN`: 평균보다 극단값에 덜 흔들린다.

### 4-3. `sql/08_recommendation.sql`: 결론이 견고한가

```sql
SELECT car_profile, time_value, summer_plan,
       CASE WHEN COUNT(DISTINCT option) = 1 THEN MODE(option) || ' (robust)'
            ELSE MODE(option) || ' (depends on rent estimate)' END AS recommendation,
       STRING_AGG(rent_method || '=' || option, ', ' ORDER BY rent_method) AS detail
FROM winners
GROUP BY car_profile, time_value, summer_plan
ORDER BY CASE car_profile WHEN 'transit' THEN 1 WHEN 'drives_owned' THEN 2 ELSE 3 END, ...
```
- `COUNT(DISTINCT option) = 1`: 세 렌트 추정 방식에서 모두 같은 선택이 이겼다 → robust.
- `MODE()`: 최빈값. `STRING_AGG`: 그룹 안의 값을 문자열 하나로 (MySQL은 `GROUP_CONCAT`).
- `ORDER BY CASE …`: 알파벳순이 아닌 원하는 순서로 정렬.

### 4-4. `sql/11_time_value_breakeven.sql`: 손익분기 시간 가치

```sql
-- 동네가 더 싸려면: cash_nb + 9·hours_nb·v < cash_ucla + 9·hours_ucla·v
--                ⇔ v < (cash_ucla − cash_nb) / (9 · (hours_nb − hours_ucla))
SELECT c.car_profile, c.summer_plan, c.option AS neighborhood,
       ROUND(u.ucla_cash - c.cash_cost) AS cash_savings_vs_ucla,
       CASE WHEN u.ucla_cash - c.cash_cost <= 0 THEN NULL
            ELSE ROUND((u.ucla_cash - c.cash_cost) / (9 * (h.hours_per_school_month - u.ucla_hours)), 1)
       END AS breakeven_usd_per_hour
FROM cash c
JOIN ucla u USING (summer_plan, car_profile)
JOIN hours h ON h.option = c.option AND h.car_profile = c.car_profile
```
- `time_value = 0`인 시나리오 행이 곧 "현금 비용만"이다. 이미 만든 테이블을 재활용했다.
- 부등식을 v에 대해 풀어 SQL 식 하나로 썼다. 분석에서 "정답 없는 값(시간 가치)"을 **기준선**으로 바꾸는 방법이다.
- `CASE … THEN NULL`: 현금으로도 더 비싸면 어떤 시간 가치에서도 이길 수 없으므로 NULL. 0으로 나누기나 음수 손익분기 같은 의미 없는 값을 막는다.
- `JOIN ... USING (summer_plan, car_profile)`: 여러 컬럼으로 JOIN할 때도 USING을 쓸 수 있다.

### 직접 해 보기
1. `06`의 time_value에 `(10.0)`을 추가하고 07 결과에서 Koreatown 승률이 어떻게 바뀌는지 보자.
2. `06`의 ④에서 GROUP BY를 지우고 `pp`를 그대로 쓰면 UCLA 행이 몇 개가 되는지 세어 보자.

---

## 5단계. 추이, 차트, 내보내기

### 5-1. `sql/09_trend_summary.sql`: 동네별 연도 요약

```sql
SELECT zip, area, year, months, ROUND(avg_rent) AS avg_rent,
       ROUND(100 * (avg_rent / LAG(avg_rent) OVER (PARTITION BY zip ORDER BY year) - 1), 1) AS growth_pct,
       ROUND(100 * avg_rent / FIRST_VALUE(avg_rent) OVER (PARTITION BY zip ORDER BY year), 1) AS index_2018,
       ROUND(100 * (MAX(CASE WHEN zip = '90024' THEN avg_rent END) OVER (PARTITION BY year) / avg_rent - 1), 1)
         AS westwood_premium_pct
FROM yearly
```
- `COUNT(*) AS months`(yearly CTE): 2026년은 10개월뿐이라 불완전한 해임을 표시.
- 한 쿼리에 **PARTITION 기준이 다른 윈도우 세 개**: ZIP별 전년 값(`PARTITION BY zip`), ZIP별 첫해 값(지수), 연도별 Westwood 값(`PARTITION BY year`).
- `FIRST_VALUE`: 정렬 순서의 첫 값 = 2018년. 매년 값을 2018년으로 나누면 **지수(2018 = 100)**. 출발점이 다른 동네의 상승 속도를 비교할 때 쓴다.

### 5-2. `sql/10_premium_seasonality.sql`: 추세를 빼고 계절성만 보기

```sql
WITH monthly AS (
    SELECT month,
           100 * (MAX(CASE WHEN zip = '90024' THEN zori END)
                / AVG(CASE WHEN zip <> '90024' THEN zori END) - 1) AS premium_pct
    FROM zori WHERE month >= DATE '2018-01-01'
    GROUP BY month
),
deviation AS (
    SELECT month, premium_pct - AVG(premium_pct) OVER (PARTITION BY YEAR(month)) AS gap_vs_year_avg
    FROM monthly
)
SELECT MONTH(month) AS calendar_month, ROUND(AVG(gap_vs_year_avg), 2) AS avg_gap_pctpt,
       SUM(CASE WHEN gap_vs_year_avg > 0 THEN 1 ELSE 0 END) AS years_above_avg
FROM deviation GROUP BY MONTH(month)
```
- **조건부 집계 두 개를 나눈다**: `MAX(CASE WHEN zip = '90024' …)`(Westwood)를 `AVG(CASE WHEN zip <> '90024' …)`(나머지 6곳 평균)로 나눠 월별 프리미엄을 만든다. 피벗과 같은 원리다.
- `AVG(...) OVER (PARTITION BY YEAR(month))`: 각 달 옆에 그해 평균을 붙여 빼면 장기 추세가 빠지고 "그해 평균보다 얼마나 높은가"만 남는다.
- `years_above_avg`: "9년 중 몇 해나 평균보다 높았나". 평균 하나보다 패턴이 일관적인지를 보여준다.

### 5-3. `scripts/05_make_charts.py`: 차트

```python
COLOR = {"Westwood": "#2a78d6", "West LA / Sawtelle": "#eb6834", "UCLA": "#1baf7a", ...}
```
- **선택지별 색을 고정**해서 모든 차트에서 같은 대상은 같은 색.

```python
ys, min_gap = [], 70
for _, r in last.iterrows():                     # 최신 렌트가 낮은 동네부터
    y = r["rent"] if not ys else max(r["rent"], ys[-1] + min_gap)
    ys.append(y)
    ax.annotate(f"{r['area']}  ${r['rent']:,.0f}", (r["month"], y), xytext=(8, 0), textcoords="offset points")
```
- 선 끝에 이름과 값을 직접 단다(direct label). 7개 선의 끝 값이 가까우면 글자가 겹치므로, 아래부터 올라가며 최소 간격($70)만큼 밀어 올린다.

```python
ax.barh(y, m["annual_rent"], label="Rent")
ax.barh(y, m["annual_commute_cost"], left=m["annual_rent"], label="Commute time ($20/hr)")
```
- **누적 가로 막대**: `left=`에 앞 막대의 끝을 넣으면 그 뒤에 이어 그린다. 렌트와 통학 비용이 각각 얼마인지, 합계가 얼마인지 한 번에 보인다.

```python
share = (w[w["car_profile"] == prof].groupby("time_value")["option"]
         .value_counts(normalize=True).mul(100).unstack(fill_value=0))
```
- `value_counts(normalize=True)`: 비율. `unstack`: 긴 형태 → 넓은 형태(시간 가치 × 선택지 표). 100% 누적 막대를 그리기 좋은 모양이다.
- 단위가 다른 값을 한 차트에 축 두 개로 겹치지 않고, 통학 방식별로 패널을 나눴다(small multiples).

### 5-4. `scripts/06_tableau_export.py`: 대시보드용 데이터

```python
s = s.merge(occ, on="unit_type", how="left")
s["time_value_label"] = s["time_value"].map(lambda v: f"${v:.0f}/hr")
s["is_cheapest"] = (s["cost_rank"] == 1).astype(int)
```
- `merge(..., how="left")`: SQL의 LEFT JOIN. 시나리오 표에 인원 수를 붙인다.
- 숫자 코드(`time_value = 20.0`)를 사람이 읽는 라벨(`$20/hr`)로 바꿔 두면 Tableau 필터가 바로 읽힌다.
- `is_cheapest` 0/1 플래그: Tableau에서 `SUM`은 승리 횟수, `AVG`는 승률. GA4 프로젝트의 0/1 플래그와 같은 아이디어.

---

## 이 프로젝트에서 쓴 SQL 패턴 모음 (쿼리 테스트 대비)

| 패턴 | 쓴 곳 | 한 줄 요약 |
| --- | --- | --- |
| `LAG / LEAD` | 02, 07, 09 | 앞·뒤 행 값 (전년 대비, 1등과 2등 차이) |
| 기준값을 윈도우로 붙이기 `MAX(CASE…) OVER (PARTITION BY month)` | 02, 09 | 지역 수와 무관하게 "기준 대비 %" 계산 |
| `MAX(CASE WHEN …)` 조건부 집계 / 피벗 | 03, 10 | 조건에 맞는 값만 집계 |
| `ROW_NUMBER` + `QUALIFY` | 03 | 그룹별 최신·최고 1개 |
| 집계 없는 윈도우 | 03, 10 | 그룹 값을 모든 행 옆에 붙이기 |
| 스칼라 서브쿼리 | 05 | 가정값 테이블에서 값 하나 읽기 |
| `UNION ALL`로 경우 쌓기 | 04, 05, 06 | 계산식이 다른 경우들을 긴 형태로 합치기 |
| `CROSS JOIN` + `VALUES` | 06 | 시나리오 조합 만들기 |
| `WHERE … OR (… AND …)` | 06 | 조건별 허용 규칙 (괄호 필수) |
| GROUP BY로 JOIN 팽창 접기 | 06 | 중복 행 방지 |
| 파라미터 CTE | 04, 05 | 가정값을 한 곳에 모으기 |
| `RANK` (다차원 PARTITION) | 04, 06 | 같은 시나리오 안의 순위 |
| `SUM(COUNT(*)) OVER` | 07 | 집계 결과 위에서 비율 |
| `COUNT(DISTINCT) = 1` | 08 | 모든 조건에서 결과가 같은지 |
| 부등식을 풀어 손익분기 계산 | 11 | 정답 없는 값을 기준선으로 |
| `FIRST_VALUE` | 09 | 기준 시점 대비 지수 |
| `CASE` 정렬 | 08 | 원하는 순서로 정렬 |
