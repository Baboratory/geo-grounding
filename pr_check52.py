import json, urllib.request

def get_token():
    with open('/workspace/.gh_token.env') as f:
        for line in f:
            if '=' in line:
                return line.split('=',1)[1].strip()
    return None

tok = get_token()
def gh(u):
    r = urllib.request.Request(u, headers={'Authorization': f'Bearer {tok}', 'User-Agent':'curl'})
    return json.load(urllib.request.urlopen(r))

# Locate highest-numbered open PR and show its mergeable state
prs = gh('https://api.github.com/repos/Baboratory/geo-grounding/pulls?state=open&per_page=5&sort=created&direction=desc')
for p in prs:
    n = p['number']
    ind = gh(f'https://api.github.com/repos/Baboratory/geo-grounding/pulls/{n}')
    print('PR#', n, p['head']['ref'], 'title:', p['title'])
    print('  mergeable:', ind.get('mergeable'), ind.get('mergeable_state'))
    try:
        files = gh(p['url'] + '/files')
        print('  files:', [f['filename'] for f in files])
    except Exception as e:
        print('  files ERR', e)

# Count data/countries dirs on latest batch-52 branch
import subprocess
print('--- batch-52 pyproject setuptools ---')
print(subprocess.run(['git','show','batch-52/add-rus-ukr:pyproject.toml'],capture_output=True,text=True).stdout.count('setuptools'))
print('--- countries on batch-52 ---')
print(subprocess.run(['git','ls-tree','batch-52/add-rus-ukr','data/countries/','--name-only'],capture_output=True,text=True).stdout.count('/'))