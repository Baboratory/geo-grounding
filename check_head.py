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

d = gh("https://api.github.com/repos/Baboratory/geo-grounding/pulls/53")
print("PR head ref:", d['head']['ref'])
print("PR head sha:", d['head']['sha'])
print("PR base sha:", d['base']['sha'])
# Local clean commit sha
import subprocess
print("local batch-53-clean sha:", subprocess.run(['git','rev-parse','batch-53-clean'], capture_output=True, text=True).stdout.strip())
print("fork/remote sha:", subprocess.run(['git','rev-parse','fork/batch-53/add-sau-are-yem'], capture_output=True, text=True).stdout.strip())