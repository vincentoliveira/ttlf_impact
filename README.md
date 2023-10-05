# TTFL Lab Impact

## How to run TTFL Lab Impact

```bash
python -m venv venv
source env/bin/activate
pip install -r requirements.txt
python main.py  
```

How to use command line
```commandline
main.py -d <day_to_generate> -f <force_refresh> -s <season> -t <season_type>
        <day_to_generate> mm/dd/yyyy (default: today)
        <force_refresh> True or False (default: False)
        <season> yyyy-yy (default: 2022-23)
        <season_type> RegularSeason, PlayOff (default: RegularSeason)
```

## How does is work
1. Refresh database (team, player and box scores)
2. Fetch daily games
3. Compute impact and inject data into [impact_template.xlsx](impact_template.xlsx) files
4. 