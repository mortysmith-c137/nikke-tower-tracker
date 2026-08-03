# NIKKE Tower Tracker

A small desktop companion for **GODDESS OF VICTORY: NIKKE** players who want to keep track of Manufacturer Tower progress and estimate when they will have enough molds for their next pull.

Enter the last floor you reached, your mold count, and the number of openings you want to prepare for. The tracker calculates the floors needed, applies the bonus reward on every fifth floor, and accounts for each tower's weekly opening schedule.

## Features

- Tracks Elysion, Missilis, Tetra, and Pilgrim towers in one window
- Calculates the next 50-mold threshold for one or more requested openings
- Applies normal and fifth-floor bonus mold rewards
- Estimates the real calendar time based on the selected day of the week
- Shows a floor-by-floor breakdown for every calculation
- Saves your latest inputs locally, so they are ready the next time you open the app
- Exports calculation results as timestamped TXT reports

## Requirements

- Python 3.10 or newer
- PySide6

## Download

Download the latest ready-to-run executable from the [Releases](https://github.com/mortysmith-c137/nikke-tower-tracker/releases) section.

## Run from Source

Clone the repository and create a virtual environment if you would like to keep the dependency isolated:

```bash
git clone https://github.com/mortysmith-c137/nikke-tower-tracker.git
cd nikke-tower-tracker
```

Install the dependency and start the app:

```bash
pip install -r requirements.txt
python main.py
```

## How it works

1. Choose the current day of the week.
2. For each tower, enter the last floor you reached, your current mold total, and how many openings you want to reach.
3. Select **Calculate** to see the target floor, expected molds, and estimated completion time.
4. Use **Create TXT Report** if you want to keep a copy of the result.

The calculator starts with the floor after the last one you reached. A standard floor gives one mold, while every fifth floor gives five. Towers can be cleared for up to three floors on days when they are open.

## Local files

The application creates a few files beside the source code or packaged executable:

- `data.json` stores the selected day and tower inputs.
- `reports/` contains exported TXT reports.

Both are local, generated files and are intentionally excluded from version control.
