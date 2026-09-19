#!/usr/bin/env python3
files = ["data/countries/RUS/distinct-regions/ru-spe.yaml"]
for f in files:
    with open(f,'rb') as fh:
        data = fh.read()
    if not data.endswith(b'\n'):
        with open(f,'ab') as fh:
            fh.write(b'\n')
        print("added NL:", f)
    else:
        print("ok      :", f)
print("done")