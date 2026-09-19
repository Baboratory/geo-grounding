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
    return json.load(urllib.request.urlopen(req))

# GitHub's view of the fork branch ref
refs = gh("https://api.github.com/repos/devContributor/geo-grounding/git/refs/heads/batch-53/add-sau-are-yem")
print("fork branch ref sha (GitHub's view):", refs['object']['sha'])
# PR again
d = gh("https://api.github.com/repos/Baboratory/geo-grounding/pulls/53")
print("PR head sha:", d['head']['sha'])
print("match:", refs['object']['sha'] == d['head']['sha'])