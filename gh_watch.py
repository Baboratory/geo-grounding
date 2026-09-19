import json, urllib.request, time
tok = [l for l in open('/workspace/.gh_token.env') if '=' in l][0].split('=',1)[1].strip()
def gh(url):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {tok}', 'Accept':'application/vnd.github+json'})
    return json.load(urllib.request.urlopen(req))
time.sleep(8)
runs = gh('https://api.github.com/repos/Baboratory/geo-grounding/actions/runs?per_page=6')
target = None
for x in runs.get('workflow_runs', []):
    if x['head_branch']=='batch-52/add-rus-ukr':
        print("run", x['id'], x['status'], x['conclusion'], x['head_sha'][:7])
        if x['status']=='in_progress':
            target = x['id']
if target:
    for i in range(28):
        time.sleep(20)
        r = gh(f'https://api.github.com/repos/Baboratory/geo-grounding/actions/runs/{target}')
        print("  ...", r['status'], r['conclusion'])
        if r['status']=='completed':
            # print step conclusions
            j = gh(f'https://api.github.com/repos/Baboratory/geo-grounding/actions/runs/{target}/jobs')
            for job in j.get('jobs', []):
                for s in job.get('steps', []):
                    print("   step:", s['name'], '->', s['conclusion'])
            break
else:
    print("no in_progress run yet")