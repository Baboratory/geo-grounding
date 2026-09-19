import json, urllib.request
tok = [l for l in open('/workspace/.gh_token.env') if '=' in l][0].split('=',1)[1].strip()
j = json.load(urllib.request.urlopen(urllib.request.Request(
    'https://api.github.com/repos/Baboratory/geo-grounding/actions/runs/35499081504/jobs',
    headers={'Authorization':'Bearer '+tok})))
for job in j.get('jobs', []):
    print("job:", job['name'], job['conclusion'])
    for s in job.get('steps', []):
        print("   step:", s['name'], '->', s['conclusion'], s.get('number'))