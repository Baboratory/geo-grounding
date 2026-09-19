import json, urllib.request
tok = [l for l in open('/workspace/.gh_token.env') if '=' in l][0].split('=',1)[1].strip()
def gh(url):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {tok}', 'Accept':'application/vnd.github+json'})
    return json.load(urllib.request.urlopen(req))
# the failing run
r = gh('https://api.github.com/repos/Baboratory/geo-grounding/actions/runs/35499081504')
print("run:", r['name'], r['status'], r['conclusion'], '| head_sha:', r['head_sha'], '| event:', r['event'], '| pr:', r.get('pull_requests'))
print("branch:", r['head_branch'])
# recent runs for the validate workflow
runs = gh('https://api.github.com/repos/Baboratory/geo-grounding/actions/runs?per_page=15')
for x in runs.get('workflow_runs', []):
    print(x['id'], x['name'], x['head_branch'][:30], x['status'], x['conclusion'], x['head_sha'][:7], x['event'])