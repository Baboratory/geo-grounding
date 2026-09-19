#!/usr/bin/env python3
import subprocess
files = [
 "data/languages/tat.yaml","data/languages/sah.yaml",
 "data/countries/RUS/country.yaml","data/countries/RUS/distinct-regions/whole.yaml",
 "data/countries/RUS/distinct-regions/ru-mow.yaml","data/countries/RUS/distinct-regions/ru-ta.yaml",
 "data/countries/RUS/distinct-regions/ru-sa.yaml","data/countries/RUS/distinct-regions/ru-spe.yaml",
 "data/countries/UKR/country.yaml","data/countries/UKR/distinct-regions/whole.yaml",
 "data/countries/UKR/distinct-regions/ua-30.yaml","data/countries/UKR/distinct-regions/ua-46.yaml",
 "data/countries/UKR/distinct-regions/ua-51.yaml","data/countries/UKR/distinct-regions/ua-63.yaml",
]
for f in files:
    out = subprocess.run(['git','show',f'HEAD:{f}'], capture_output=True, text=True).stdout
    if not out.endswith('\n'):
        print("NO TRAILING NL:", f)
    else:
        print("ok:", f)
print("check done")