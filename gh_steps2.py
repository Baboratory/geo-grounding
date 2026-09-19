import json, urllib.request
tok = [l for l in open('/workspace/.gh_token.env') if '=' in l][0].split('=',1)[1].strip()
def gh(url):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {tok}', 'Accept':'application/vnd.github+json'})
    return json.load(urllib.request.urlopen(req))
for runid in ['35499229610']:
    j = gh(f'https://api.github.com/repos/Baboratory/geo-grounding/actions/runs/{runid}/jobs')
    for job in j.get('jobs', []):
        print("job:", job['name'], job['conclusion'])
        for s in job.get('steps', []):
            print("   step:", s['name'], '->', s['conclusion'], s.get('number'))