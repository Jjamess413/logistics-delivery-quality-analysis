"""Run portable rule/query checks; optionally run the official Power BI CLI."""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import re
import shutil
import subprocess
import unittest

from run_queries import main as run_queries

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--powerbi-cli');args=parser.parse_args()
    source=json.loads((ROOT/'reports/validation.json').read_text())
    assert source['passed'] is True
    assert hashlib.sha256((ROOT/'data/processed/fact_delivery.csv').read_bytes()).hexdigest()==source['fact_sha256']
    tests=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    result=unittest.TextTestRunner(verbosity=1).run(tests)
    rules={'passed':result.wasSuccessful(),'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
      'scope':'Hand-calculated delivery, exclusion, child-join and review-selection fixtures'}
    (ROOT/'reports/business_rule_validation.json').write_text(json.dumps(rules,indent=2)+'\n')
    if not result.wasSuccessful():raise SystemExit(1)
    run_queries()
    for p in (ROOT/'scripts').glob('*.py'):ast.parse(p.read_text())
    cli=args.powerbi_cli or shutil.which('powerbi-report-author')
    if cli:
        version=subprocess.run([cli,'--version'],capture_output=True,text=True,check=True).stdout.strip()
        checked=subprocess.run([cli,'validate',str(ROOT/'powerbi/LogisticsDelivery.pbip'),'--no-schema'],capture_output=True,text=True,check=True)
        data=json.loads(checked.stdout)['data']
        report={'passed':data['result']=='succeeded','tool':'@microsoft/powerbi-report-authoring-cli','tool_version':version,
          'result':data['result'],'error_count':data['errorCount'],'warning_count':data['warningCount'],
          'scope':'Offline project conformance, not native Desktop execution'}
        (ROOT/'reports/powerbi_cli_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    broken=[]
    for p in [ROOT/'README.md',ROOT/'START_HERE.md',ROOT/'dashboard/README.md']:
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if not link.startswith(('http:','https:','#')) and not (p.parent/link.split('#')[0]).exists():broken.append([str(p.relative_to(ROOT)),link])
    if broken:raise AssertionError(broken)
    print(json.dumps({'passed':True,'unit_tests':result.testsRun,'markdown_links':'PASS','python_syntax':'PASS','official_cli_executed':bool(cli)}))


if __name__=='__main__':main()
