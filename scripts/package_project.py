"""Build a checked portable deliverable without raw data, screenshots or caches."""
from pathlib import Path
import argparse
import json
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'dist/James_You_Logistics_Delivery_Project.zip');args=parser.parse_args()
    for name in ['validation.json','query_validation.json','business_rule_validation.json','dashboard_data_validation.json','browser_validation.json','powerbi_source_validation.json','powerbi_cli_validation.json']:
        if json.loads((ROOT/'reports'/name).read_text()).get('passed') is not True:raise SystemExit('Required validation has not passed: '+name)
    files={ROOT/name for name in ['README.md','START_HERE.md','DATA_ATTRIBUTION.md','LICENSE','requirements.txt','config.json','OPEN_POWERBI.cmd','package.json','.gitignore','data/README.md']}
    for directory in ['scripts','sql','docs','reports','tests','powerbi','dashboard']:
        for p in (ROOT/directory).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and '.pbi' not in p.parts and p.suffix.lower() not in ['.png','.jpg','.jpeg']:
                files.add(p)
    for name in ['fact_delivery.csv','dim_date.csv','dim_state.csv','dim_category.csv','logistics.sqlite']:
        p=ROOT/'data/processed'/name
        if not p.exists():raise SystemExit('Missing local input: '+name)
        files.add(p)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    prefix='James_You_Logistics_Delivery_Project'
    with zipfile.ZipFile(args.output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for p in sorted(files):
            name=(Path(prefix)/p.relative_to(ROOT)).as_posix()
            if p==ROOT/'README.md':
                text=p.read_text();text='\n'.join(line for line in text.splitlines() if not line.startswith('!['))
                text=text.replace('The screenshots here are actual captures of the browser report. Native Desktop captures are not yet available.','This package contains the working browser report. Native Desktop captures are not yet available.')
                archive.writestr(name,text+'\n')
            else:archive.write(p,name)
    with zipfile.ZipFile(args.output) as archive:
        assert archive.testzip() is None
        assert not any('/data/raw/' in n or '/.git/' in n or '/.pbi/' in n for n in archive.namelist())
    print(json.dumps({'passed':True,'files':len(files),'bytes':args.output.stat().st_size,'output':str(args.output.resolve()),'raw_data_included':False,'native_desktop_execution':'Pending owner confirmation'},indent=2))


if __name__=='__main__':main()
