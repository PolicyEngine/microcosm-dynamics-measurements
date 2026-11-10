# Build a claim-age model

You are building one module of a retirement model: the age at which people first claim a retirement benefit.

- `data/claims.csv` holds one row per person: `person_id`, `birth_year` (1940 to 1958), `female` (0 or 1), `earnings_tercile` (1 to 3) and `claim_age` (62 to 70).
- `references/` holds background reading from the project's files.

## Deliver

1. `predict.py`: fits your model on `data/claims.csv` and writes `prediction.csv`.
2. `prediction.csv`: for people born in 1962, the share who claim at each age. Columns `claim_age` (62 to 70) and `share` (the nine shares sum to 1), for all persons combined, with equal weight on each sex-by-tercile group.
3. `MODEL.md`: at most 200 words on your model and each choice you made, including how you extrapolated from the 1940 to 1958 cohorts to 1962.

## Rules

- Your prediction must come from the data in `data/`. Don't calibrate it to any outside figure.
- A hidden record of the 1962 cohort scores your prediction once. You get no feedback.
- Work only in this folder. Open nothing outside it, and use no web access.
- Run Python as `uv run --with pandas --with numpy --with scikit-learn --with statsmodels python predict.py`.
- If `uv` can't run in your sandbox, use `python3` with the standard library and say so in `MODEL.md`.
- Run `predict.py` once at the end and check that `prediction.csv` has nine rows. Give each share to at least four decimal places.
- Don't commit, push or post.

## Report

Your final message gives the nine shares and one sentence on how you extrapolated.
