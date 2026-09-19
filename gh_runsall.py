import json, urllib.request
tok = [l for l in open('/workspace/.gh_token.env') if '=' in l][0].split('=',1)[1].strip()
def gh(url):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {tok}', 'Accept':'application/vnd.github+json'})
    return json.load(urllib.request.urlopen(req))
runs = gh('https://api.github.com/repos/Baboratory/geo-grounding/actions/runs?per_page=20')
for x in runs.get('workflow_runs', []):
    print(x['id'], x['head_branch'][:35], x['status'], x['conclusion'], x['head_sha'][:7], x['created_at'])