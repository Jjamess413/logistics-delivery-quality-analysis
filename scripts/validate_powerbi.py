"""Validate public PBIR schemas, resources, bindings, fields and CSV row counts."""
from pathlib import Path
import csv
import hashlib
import json
import tempfile
import urllib.parse
import urllib.request
import warnings
from jsonschema import Draft7Validator, RefResolver

ROOT=Path(__file__).resolve().parents[1]
CACHE=Path(tempfile.gettempdir())/'inventory-portfolio-schemas'
SCHEMAS={}


def fetch(url):
    url=urllib.parse.urldefrag(url)[0].replace('/schema.embedded.json','/schema-embedded.json')
    if url in SCHEMAS:return SCHEMAS[url]
    if not url.startswith('https://developer.microsoft.com/json-schemas/'):raise ValueError('Unexpected schema source')
    path=CACHE/(hashlib.sha256(url.encode()).hexdigest()+'.json')
    if path.exists():value=json.loads(path.read_text())
    else:
        with urllib.request.urlopen(url,timeout=30) as r:value=json.load(r)
        CACHE.mkdir(exist_ok=True);path.write_text(json.dumps(value))
    SCHEMAS[url]=value
    return value


def refs(value):
    if isinstance(value,dict):
        for kind in ['Column','Measure']:
            if kind in value:
                field=value[kind];table=field.get('Expression',{}).get('SourceRef',{}).get('Entity')
                if table:yield kind,table,field['Property']
        for item in value.values():yield from refs(item)
    elif isinstance(value,list):
        for item in value:yield from refs(item)


def main():
    errors=[];documents=0
    for path in (ROOT/'powerbi').rglob('*'):
        if not path.is_file() or (path.suffix not in ['.json','.pbip','.pbir','.pbism'] and path.name!='.platform'):continue
        value=json.loads(path.read_text());url=value.get('$schema')
        if not url:continue
        schema=fetch(url)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',DeprecationWarning)
            validator=Draft7Validator(schema,resolver=RefResolver(base_uri=url,referrer=schema,handlers={'https':fetch}))
            for error in validator.iter_errors(value):errors.append({'file':str(path.relative_to(ROOT)),'message':error.message})
        documents+=1
    report=ROOT/'powerbi/LogisticsDelivery.Report';definition=report/'definition'
    if json.loads((definition/'version.json').read_text())['version']!='2.0.0':errors.append({'message':'Unexpected content version'})
    if not (report/'.platform').exists():errors.append({'message':'Missing platform metadata'})
    pages={p.parent.name:json.loads(p.read_text()) for p in (definition/'pages').glob('*/page.json')}
    order=json.loads((definition/'pages/pages.json').read_text())['pageOrder']
    if len(pages)!=3 or set(order)!=set(pages) or any(k!=v['name'] for k,v in pages.items()):errors.append({'message':'Page folder/index mismatch'})
    meta=json.loads((definition/'report.json').read_text())
    for package in meta.get('resourcePackages',[]):
        for item in package.get('items',[]):
            if not (report/'StaticResources'/package['name']/item['path']).exists():errors.append({'message':'Missing resource '+item['path']})
    model=json.loads((ROOT/'powerbi/LogisticsDelivery.SemanticModel/model.bim').read_text())['model']
    tables={x['name']:x for x in model['tables']};references=0;csv_checks={}
    sources={'FactDelivery':'fact_delivery.csv','DimDate':'dim_date.csv','DimState':'dim_state.csv','DimCategory':'dim_category.csv'}
    for name,filename in sources.items():
        with (ROOT/'data/processed'/filename).open(newline='') as f:
            reader=csv.DictReader(f);headers=set(reader.fieldnames);rows=sum(1 for _ in reader)
        needed={x['sourceColumn'] for x in tables[name]['columns']}
        csv_checks[name]={'rows':rows,'columns_present':needed<=headers}
        if not needed<=headers:errors.append({'message':'Missing CSV columns for '+name})
    if csv_checks['FactDelivery']['rows']!=json.loads((ROOT/'reports/summary.json').read_text())['orders']:errors.append({'message':'Fact count mismatch'})
    for path in report.rglob('visual.json'):
        for kind,table,name in refs(json.loads(path.read_text())):
            known=tables.get(table,{}).get('columns' if kind=='Column' else 'measures',[])
            if name not in {x['name'] for x in known}:errors.append({'file':str(path.relative_to(ROOT)),'message':'Unknown field '+table+'.'+name})
            references+=1
    if len(model['relationships'])!=3 or any(r['crossFilteringBehavior']!='oneDirection' for r in model['relationships']):errors.append({'message':'Unexpected relationships'})
    result={'passed':not errors,'json_documents':documents,'field_references':references,'pages':len(pages),
      'visuals':len(list(report.rglob('visual.json'))),'tables':len(tables),'measures':sum(len(t.get('measures',[])) for t in tables.values()),
      'csv_checks':csv_checks,'errors':errors,'scope':'Public source format, model bindings and inputs; not Desktop rendering or DAX execution',
      'desktop_status':'Pending owner Windows refresh and screenshots'}
    (ROOT/'reports/powerbi_source_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
