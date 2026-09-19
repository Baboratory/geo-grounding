#!/usr/bin/env python3
import sys
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
    with open(f,'rb') as fh:
        data = fh.read()
    if not data.endswith(b'\n'):
        with open(f,'ab') as fh:
            fh.write(b'\n')
        print("added NL:", f)
    else:
        print("ok      :", f)
for f in files:
    with open(f,'rb') as fh:
        fh.seek(-1,2); tail = fh.read(1)
    assert tail == b'\n', f"NO TRAILING NL {f}"
print("ALL have trailing newline")