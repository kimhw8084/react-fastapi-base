#!/usr/bin/env python3
"""Capture deterministic widget fixtures from their real constructors for React stories.
Generated JSON is NOT an additional hand-maintained source of business data.
"""
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'experience-lab/tests'))
from browser_loader import load_lab
from playwright.sync_api import sync_playwright

def main():
    os.environ['LAB_BROWSER_MODE']='in_memory'
    entries=json.loads((ROOT/'catalog/components.json').read_text())['entries']
    with sync_playwright() as pw:
        kwargs={'headless':True}
        chromium=os.environ.get('LAB_CHROMIUM_PATH','/usr/bin/chromium')
        if Path(chromium).is_file():kwargs['executable_path']=chromium
        browser=pw.chromium.launch(**kwargs);page=browser.new_page();load_lab(page)
        fixtures={}
        for entry in entries:
            page.evaluate('(id)=>window.location.hash="/"+id',entry['id'])
            page.wait_for_selector(entry['tag'])
            fixtures[entry['id']]=page.locator(entry['tag']).evaluate('(el)=>el.model')
        browser.close()
    path=ROOT/'catalog/examples.json';path.write_text(json.dumps(fixtures,indent=2)+'\n')
    print(f'Captured {len(fixtures)} deterministic synthetic widget models.')
if __name__=='__main__':main()
