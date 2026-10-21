"""Set the local processed-input path and open the authored native project."""
from pathlib import Path
import argparse
import json
import os

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true');args=parser.parse_args()
    folder=ROOT/'data/processed'
    missing=[name for name in ['fact_delivery.csv','dim_date.csv','dim_state.csv','dim_category.csv'] if not (folder/name).is_file()]
    if missing:raise SystemExit('Missing local inputs: '+', '.join(missing)+'. Extract the full portable package or run scripts/build.py first.')
    report=ROOT/'powerbi/LogisticsDelivery.Report';definition=report/'definition'
    version=json.loads((definition/'version.json').read_text())['version']
    pages=json.loads((definition/'pages/pages.json').read_text())['pageOrder']
    if version!='2.0.0' or not (report/'.platform').is_file() or len(pages)!=3 or any(not (definition/'pages'/p/'page.json').exists() for p in pages):
        raise SystemExit('The report layout is incomplete. Extract the full ZIP into a new folder.')
    meta=json.loads((definition/'report.json').read_text())
    for package in meta.get('resourcePackages',[]):
        for item in package.get('items',[]):
            if not (report/'StaticResources'/package['name']/item['path']).is_file():raise SystemExit('Report theme resource missing. Extract the full ZIP.')
    path=ROOT/'powerbi/LogisticsDelivery.SemanticModel/model.bim'
    model=json.loads(path.read_text(encoding='utf-8'))
    parameter=next(x for x in model['model']['expressions'] if x['name']=='pDataFolder')
    parameter['expression']='"'+folder.resolve().as_posix().replace('"','""')+'/" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
    path.write_text(json.dumps(model,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Configured input folder:',folder.resolve())
    print('Three report pages and registered resources checked. Open the project, click Refresh and compare START_HERE.md.')
    if os.name=='nt' and not args.prepare_only:os.startfile(str(ROOT/'powerbi/LogisticsDelivery.pbip'))


if __name__=='__main__':main()
