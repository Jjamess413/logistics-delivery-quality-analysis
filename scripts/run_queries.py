from pathlib import Path
import json
import sqlite3

ROOT=Path(__file__).resolve().parents[1]


def main():
    statements=[]
    buffer=''
    for line in (ROOT/'sql/02_business_queries.sql').read_text().splitlines(keepends=True):
        buffer+=line
        if sqlite3.complete_statement(buffer):
            statements.append(buffer)
            buffer=''
    output=[]
    validation=[]
    with sqlite3.connect(ROOT/'data/processed/logistics.sqlite') as db:
        for statement in statements:
            if not statement.strip(): continue
            cursor=db.execute(statement)
            if cursor.description is None: continue
            rows=cursor.fetchall()
            number=len(validation)+1
            validation.append({'query':number,'rows':len(rows)})
            output.append('QUERY '+str(number)+'\n'+' | '.join(x[0] for x in cursor.description))
            output.extend(' | '.join('NULL' if x is None else str(x) for x in row) for row in rows)
            output.append('')
    (ROOT/'reports/query_results.txt').write_text('\n'.join(output).rstrip()+'\n')
    (ROOT/'reports/query_validation.json').write_text(json.dumps({'passed':True,'queries':validation},indent=2)+'\n')
    print(json.dumps({'passed':True,'queries_executed':len(validation)}))


if __name__=='__main__': main()
