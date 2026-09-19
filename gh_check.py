import json, subprocess, sys
tok = open('/workspace/.gh_token.env').read()
tok = [l for l in tok.splitlines() if '=' in l][0].split('=',1)[1].strip()
import urllib.request
def gh(url):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {tok}'})
    return json.load(urllib.request.urlopen(req))
pulls = gh('https://api.github.com/repos/Baboratory/geo-grounding/pulls?state=open&per_page=100')
print('open PRs:', len(pulls))
for p in sorted(pulls, key=lambda x: x['number']):
    print(p['number'], '|', p['head']['ref'][:45], '| state=', p.get('state'), '| head_repo=', p['head']['repo']['full_name'] if p.get('head') and p.get('head').get('repo') else '?')
    try:
        iss = gh(f"https://api.github.com/repos/Baboratory/geo-grounding/issues/{p['number']}/comments")
        for c in iss:
            print('      comment:', c['user']['login'], ':', c['body'][:100].replace('\n',' '))
    except Exception as e:
        pass
# also check recent comments on PR #51 to see if maintainer commented
for num in [51,52,50]:
    try:
        iss = gh(f'https://api.github.com/repos/Baboratory/geo-grounding/issues/{num}/comments')
        if iss:
            print(f'--- comments on #{num}:')
            for c in iss:
                print('   ', c['user']['login'], ':', c['body'][:120].replace('\n',' '))
    except Exception as e:
        print(num, 'err', e)