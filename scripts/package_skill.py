"""Build a small, allowlisted distribution; never include corpus or private files."""
from pathlib import Path
import argparse, zipfile
ROOT=Path(__file__).resolve().parents[1]
FILES=['SKILL.md','agents/openai.yaml','scripts/query.py']
def package(output):
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for name in FILES: z.write(ROOT/'skills/cheongju-council-minutes'/name,'cheongju-council-minutes/'+name)
        z.write(ROOT/'LICENSE-CODE','cheongju-council-minutes/LICENSE')
    print(output)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');package(p.parse_args().output)
