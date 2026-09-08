"""Load exact compiled lab artifacts in a browser without external requests.

Useful for restricted CI browsers. Module specifiers are remapped to Blob URLs;
application code is otherwise unchanged. This tests the widgets, not HTTP serving.
"""
from pathlib import Path
import re,os
ROOT=Path(__file__).resolve().parents[2]
PUBLIC=ROOT/'experience-lab/public'
def load_lab(page,route='overview'):
    if os.environ.get('LAB_BROWSER_MODE','http')=='http':
        base=os.environ.get('LAB_BASE_URL')
        if not base:raise RuntimeError('LAB_BASE_URL must be supplied by the HTTP test-server fixture.')
        page.goto(base+'/#/'+route,wait_until='domcontentloaded')
        page.wait_for_selector('.lab-shell')
        return
    page.set_content('<!doctype html><html lang="en" data-theme="light"><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lab browser test</title></head><body><div id="lab-root"></div></body></html>')
    page.add_style_tag(content=(PUBLIC/'styles.css').read_text())
    modules={}
    for p in (PUBLIC/'lib').glob('*.js'):
        text=p.read_text()
        text=re.sub(r"(['\"])\./([^'\"]+\.js)\1",lambda m:repr('rfb/'+m[2]),text)
        modules['rfb/'+p.name]=text
    page.evaluate('''({modules,route})=>{
      const imports={};
      for(const [key,code] of Object.entries(modules)) imports[key]=URL.createObjectURL(new Blob([code],{type:'text/javascript'}));
      const map=document.createElement('script');map.type='importmap';map.textContent=JSON.stringify({imports});document.head.append(map);
      window.location.hash='/'+route;
      const app=document.createElement('script');app.type='module';app.textContent='import "rfb/app.js";';document.head.append(app);
    }''',{'modules':modules,'route':route})
    page.wait_for_selector('.lab-shell')
