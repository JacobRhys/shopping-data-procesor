# Supermarket Co-occurrence Explorer
This project, provides a CLI for quick queries, an embeddings system for recommendations, and a small Flask dashboard with a 3D network view.

## Repository layout
- `app/`: core logic — CSV to SQLite conversion, in-memory co-occurrence store, query helpers, embeddings, CLI loop, and 3D visualizer hooks.
- `data/`: input CSV (`Supermarket_dataset_PAI.csv`) and the generated SQLite DB (`co_occurrences.sqlite`).
- `frontend/`: Flask HTML template for the dashboard.
- `web.py`: Flask app wiring the dashboard to the co-occurrence store and embeddings.
- `tests/`: unit tests covering the store, CSV/SQLite pipeline, embeddings, and CLI behavior.
- `cuda_use.md`, `notebooks/`, `explore_data.ipynb`: notes and experiments around GPU acceleration and exploratory analysis.

## Setup
`python -m venv .venv`
`source .venv/bin/activate`
`pip install -r requirements.txt`

## Build the SQLite co-occurrence store
Generate `data/co_occurrences.sqlite` from the provided CSV (or another CSV with the same schema):
`python -m app.csv_to_sqlite data/Supermarket_dataset_PAI.csv --out data/co_occurrences.sqlite`
The CLI and web dashboard default to this path; re-run the command if you want to regenerate the DB.

## CLI usage
Start the interactive shell:
`python -m app.main`
Helpful commands once inside:
- `build [csv_path] [sqlite_out]` — compute pairs from a CSV and write SQLite.
- `load [sqlite_path]` — load a SQLite DB into memory.
- `stats` — show counts of items and pairs.
- `top_with <item> [k]`, `top_pairs [k]`, `count <item_a> <item_b>` — common queries.
- `rec_item <item> [k]`, `rec_basket <items> [k]`, `rec_customer <items> [k]` — SVD embedding recommendations.
- `visualize` — launch the interactive 3D graph viewer.

## Web dashboard
Requires a built SQLite file at `data/co_occurrences.sqlite`.
`python web.py`
Then open `http://localhost:5000` to browse top pairs, item neighbors, basket recommendations, and the 3D co-occurrence network.

## Tests
Run the test suite with:
`python -m pytest`
The tests cover the co-occurrence store, CSV/SQLite pipeline, embedding recommendations, and CLI command handling.