"""Download the publisher archive anonymously and verify pinned archive/member hashes."""
from pathlib import Path
import hashlib
import json
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ['olist_orders_dataset.csv', 'olist_order_items_dataset.csv',
         'olist_customers_dataset.csv', 'olist_order_reviews_dataset.csv',
         'olist_sellers_dataset.csv', 'olist_products_dataset.csv',
         'product_category_name_translation.csv']


def main():
    config = json.loads((ROOT/'config.json').read_text())
    raw = ROOT/'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    archive = raw/'olist_source.zip'
    if not archive.exists():
        temporary = raw/'olist_source.zip.part'
        request = urllib.request.Request(config['download_url'], headers={'User-Agent': 'JamesYou-Portfolio/1.0'})
        with urllib.request.urlopen(request, timeout=45) as source, temporary.open('wb') as target:
            while block := source.read(1024*1024):
                target.write(block)
        temporary.replace(archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != config['source_archive_sha256']:
        raise SystemExit('Publisher archive changed. Review its provenance before changing the pinned hash.')
    members = {}
    with zipfile.ZipFile(archive) as source:
        if source.testzip():
            raise SystemExit('Archive CRC check failed')
        for name in FILES:
            data = source.read(name)
            members[name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
            (raw/name).write_bytes(data)
    result = {'source': config['source_url'], 'download': config['download_url'],
              'archive_sha256': digest, 'license': config['data_license'], 'members': members}
    (ROOT/'reports/source_manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'source_integrity': 'PASS', 'members': len(members), 'archive_sha256': digest}))


if __name__ == '__main__':
    main()
