# Resident import template

Use the CSV template with UTF-8 encoding. The first three columns are required:

- `Nom`: surname
- `Prénom`: first name
- `Année`: current study year, 1–4

Phone, birth place, and birth date are optional.

## Importing documented rotation history

To import a historical stage, fill all of these columns on that resident's row:

- `Terrain`: exact department/terrain name already present in the app
- `Année universitaire`: e.g. `2024-2025`
- `Période`: e.g. `P1`, `P2`, `P3`, or `P4`
- `Date de réalisation`: optional completion date in `YYYY-MM-DD`

A resident may appear on multiple rows when each row represents a different documented stage. Repeat the resident's **current** study year in `Année` on every row; use `Année universitaire` for the historical year of each stage. Duplicate residents are matched by surname, first name and current study year; duplicate stage records are skipped. If history columns are incomplete or the terrain name is unknown, the preview displays a warning and that stage is not imported. The resident row may still be imported.

The import preview must be reviewed and explicitly confirmed. This feature never invents missing stages, years, or dates. Use only documented historical records.
