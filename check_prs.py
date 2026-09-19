import json, urllib.request

def get_token():
    with open('/workspace/.gh_token.env') as f:
        for line in f:
            if '=' in line:
                return line.split('=',1)[1].strip()
    return None

tok = get_token()
def gh(url):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {tok}', 'User-Agent':'curl/8'})
    with urllib.request.urlopen(req) as r:
        return json.load(r)

prs = gh("https://api.github.com/repos/Baboratory/geo-grounding/pulls?state=open&per_page=100")
print("OPEN PRs:", len(prs))
# Check mergeable individually + comments
for p in sorted(prs, key=lambda x: x['number']):
    n = p['number']
    # individual pull endpoint computes mergeable
    ind = gh(f"https://api.github.com/repos/Baboratory/geo-grounding/pulls/{n}")
    # issue comments (owner comments on the PR thread)
    try:
        ic = gh(f"https://api.github.com/repos/Baboratory/geo-grounding/issues/{n}/comments")
        icm = [c['user']['login'] + ': ' + c['body'][:80] for c in ic]
    except Exception as e:
        icm = [f"ERR {e}"]
    if icm and any('Baboratory' not in x for x in icm) or ind.get('mergeable') is False:
        print(f"PR#{n} {p['head']['ref']} mergeable={ind.get('mergeable')} {ind.get('mergeable_state')} comments={icm}")
print("---done---")
# also check main commit + country count
import subprocess
subprocess.run(['git','fetch','origin','main'], capture_output=True)
print(subprocess.run(['git','log','origin/main','--oneline','-3'],capture_output=True,text=True).stdout)
print(subprocess.run(['git','ls-tree','origin/main','data/','--name-only'],capture_output=True,text=True).stdout.count('.yaml')
      , 'yaml files on origin/main')