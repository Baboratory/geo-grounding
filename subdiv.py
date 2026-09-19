import pycountry
for cc in ['SA','AE','YE']:
    try:
        country = pycountry.countries.get(alpha_2=cc)
        subs = list(pycountry.subdivisions.get(country_code=cc))
        print(f"=== {cc} {country.name} ({len(subs)} subdivisions) ===")
        for s in subs[:30]:
            print(' ', s.code, '|', s.name)
        print()
    except Exception as e:
        print(cc, 'ERR', e)