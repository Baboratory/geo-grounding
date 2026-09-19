import json, urllib.request, time, subprocess

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

time.sleep(3)
d = gh("https://api.github.com/repos/Baboratory/geo-grounding/pulls/53")
print("PR head sha:", d['head']['sha'])
print("clean sha   :", subprocess.run(['git','rev-parse','batch-53-clean'],capture_output=True,text=True).stdout.strip())
files = gh("https://api.github.com/repos/Baboratory/geo-grounding/pulls/53/files")
names = [f['filename'] for f in files]
rus = [n for n in names if 'RUS' in n or 'UKR' in n or n=='data/languages/sah.yaml']
print("files:", len(names), "rusukr:", rus)
print("mergeable:", d.get('mergeable'), d.get('mergeable_state'))