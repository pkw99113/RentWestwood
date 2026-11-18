# v1 (archived): Zillow scraping + rent price model

This folder keeps the first version of the project for reference only. **Its results are not valid and are not used anywhere in v2.**

## What v1 did
- Scraped Zillow rental listings in ZIP 90024 with Selenium (`2bed2bath.py`)
- Parsed price, beds, baths, and sqft (`clean_data.py`), plotted distributions (`eda.py`)
- Trained a Random Forest to predict price per sqft (`prediction_model.py`) and wrapped it in a CLI (`rent_recommender.py`)

## Why it was retired
1. **The data could not be trusted.** Zillow's bot detection blocked most of the scraping, so only a small number of real listings were collected. The rest of the dataset was filled in with synthetic rows. Real and synthetic rows cannot be separated, so the whole dataset was removed (`zillow_properties_data.csv`, `rf_model.pkl`).
2. **The model did not beat a simple baseline.** Even on that data, the Random Forest's error (MAE about $574/month) was no better than predicting the median rent for each bedroom count (about $564/month).
3. **There was no business question.** The project predicted a number but did not say who would use it or what decision it would support.
4. **Collection method.** Scraping a site that actively blocks bots is a poor basis for a reproducible project.

## What v2 changes
v2 starts from a decision question (where should a UCLA student live?), uses only public, citable data sources, and records every data quality check. See the main [README](../../README.md).
