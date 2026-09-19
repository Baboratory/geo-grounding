import subprocess, sys
r = subprocess.run([sys.executable,'-m','pip','install','-e','.[dev]'], capture_output=True, text=True, cwd='/workspace/geo-grounding', timeout=300)
print("exit:", r.returncode)
print("=== STDOUT tail ===")
print('\n'.join(r.stdout.splitlines()[-30:]))
print("=== STDERR tail ===")
print('\n'.join((r.stderr or'').splitlines()[-30:]))