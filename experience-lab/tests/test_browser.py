"""Real Chromium interaction tests of the compiled lab; not React/PaaS certification.

The in-memory loader is for restricted CI browsers. It uses the exact compiled
module source and CSS. HTTP serving is verified separately by server tests.
"""
from pathlib import Path
import json
import os
import pytest
from playwright.sync_api import sync_playwright, expect
from browser_loader import load_lab

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/current/browser'
PAGES=['tables','boards','gantt','calendar','timeline','rack','wafer','process','charts','topology','traces','logs','diff','forms','windows','json','carrier','traveler','floorplan','permissions','split','pipeline','notifications']

@pytest.fixture(scope='session',autouse=True)
def lab_http_server():
    if os.environ.get('LAB_BROWSER_MODE','http')!='http':
        yield
        return
    import importlib.util,threading
    spec=importlib.util.spec_from_file_location('browser_lab_server',ROOT/'scripts/lab_server.py')
    server_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(server_module)
    server=server_module.make_server(0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    previous=os.environ.get('LAB_BASE_URL');os.environ['LAB_BASE_URL']=f'http://127.0.0.1:{server.server_port}'
    try:yield
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)
        if previous is None:os.environ.pop('LAB_BASE_URL',None)
        else:os.environ['LAB_BASE_URL']=previous

@pytest.fixture(scope='session')
def browser():
    with sync_playwright() as pw:
        executable=os.environ.get('LAB_CHROMIUM_PATH','/usr/bin/chromium')
        kwargs={'headless':True}
        if Path(executable).is_file():kwargs['executable_path']=executable
        browser=pw.chromium.launch(**kwargs)
        yield browser
        browser.close()

@pytest.fixture
def page(browser):
    context=browser.new_context(viewport={'width':1440,'height':1100},reduced_motion='reduce')
    page=context.new_page();page.set_default_timeout(5000)
    errors=[];page.on('pageerror',lambda error: errors.append(str(error)))
    yield page
    context.close()
    assert errors==[],f'Unhandled page errors: {errors}'

def open_page(page,route,theme='light'):
    load_lab(page,route)
    if theme=='dark':page.locator('[data-theme-toggle]').click()
    expect(page.locator('html')).to_have_attribute('data-theme',theme)

def model(page,tag):return page.locator(tag).evaluate('(el)=>el.model')

def rendered_contrast(page,selector,index=None):
    locator=page.locator(selector).nth(index) if index is not None else page.locator(selector)
    return locator.evaluate('''element=>{
      const rgb=value=>{const match=value.match(/rgba?\\(([^)]+)\\)/);if(!match)return null;const parts=match[1].split(',').map(Number);return parts.length<3?null:[parts[0],parts[1],parts[2],parts[3]??1]};
      const linear=value=>{const channel=value/255;return channel<=.03928?channel/12.92:((channel+.055)/1.055)**2.4};
      const luminance=value=>.2126*linear(value[0])+.7152*linear(value[1])+.0722*linear(value[2]);
      const foreground=rgb(getComputedStyle(element).color)||[0,0,0,1];let node=element,background=[255,255,255,1];
      while(node){const value=rgb(getComputedStyle(node).backgroundColor);if(value&&value[3]>0){background=value;break}node=node.parentElement}
      const fg=luminance(foreground),bg=luminance(background);return (Math.max(fg,bg)+.05)/(Math.min(fg,bg)+.05);
    }''')

@pytest.mark.parametrize('theme',['light','dark'])
@pytest.mark.parametrize('high_contrast',[False,True])
def test_uiqa_shared_lab_semantic_contrast(page,theme,high_contrast):
    open_page(page,'themes',theme)
    if high_contrast:page.get_by_label('High contrast',exact=True).check()
    expect(page.locator('html')).to_have_attribute('data-contrast','more' if high_contrast else 'normal')
    page.goto(page.url.replace('/themes','/timeline'))
    assert rendered_contrast(page,'.badge.tone-info')>=4.5
    state_ratios=page.locator('.state-block').evaluate_all('''elements=>elements.map(element=>{
      const rgb=value=>{const match=value.match(/rgba?\\(([^)]+)\\)/);if(!match)return null;const parts=match[1].split(',').map(Number);return parts.length<3?null:[parts[0],parts[1],parts[2],parts[3]??1]};
      const linear=value=>{const channel=value/255;return channel<=.03928?channel/12.92:((channel+.055)/1.055)**2.4};
      const lum=value=>.2126*linear(value[0])+.7152*linear(value[1])+.0722*linear(value[2]);const fg=rgb(getComputedStyle(element).color),bg=rgb(getComputedStyle(element).backgroundColor);const a=lum(fg),b=lum(bg);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
    })''')
    assert min(state_ratios)>=4.5
    assert page.locator('.state-block[aria-label]').count()==page.locator('.state-block').count()
    page.goto(page.url.replace('/timeline','/traces'))
    expect(page.locator('.trace-bar')).to_have_count(7)
    trace_ratios=page.locator('.trace-bar').evaluate_all('''elements=>elements.map(element=>{
      const rgb=value=>{const match=value.match(/rgba?\\(([^)]+)\\)/);if(!match)return null;const parts=match[1].split(',').map(Number);return parts.length<3?null:[parts[0],parts[1],parts[2],parts[3]??1]};
      const linear=value=>{const channel=value/255;return channel<=.03928?channel/12.92:((channel+.055)/1.055)**2.4};
      const lum=value=>.2126*linear(value[0])+.7152*linear(value[1])+.0722*linear(value[2]);const fg=rgb(getComputedStyle(element).color),bg=rgb(getComputedStyle(element).backgroundColor);const a=lum(fg),b=lum(bg);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
    })''')
    assert min(trace_ratios)>=4.5
    page.goto(page.url.replace('/traces','/notifications'))
    assert min(rendered_contrast(page,'.notification-item small',index) for index in range(3))>=4.5

@pytest.mark.parametrize('route',PAGES)
@pytest.mark.parametrize('theme',['light','dark'])
def test_each_registered_widget_renders(page,route,theme):
    open_page(page,route,theme)
    expect(page.locator('.engineering-widget')).to_be_visible()
    assert page.locator('.engineering-widget').inner_text().strip()
    assert page.locator('.engineering-widget [data-widget-alert]').inner_text()==''
    assert page.locator('h1').count()==1
    assert page.locator('.engineering-widget').evaluate('(el)=>el.scrollWidth>0')
    # An element must reject malformed external models, not trust TypeScript alone.
    error=page.locator('.engineering-widget').evaluate("el=>{try{el.configure(null);return ''}catch(e){return e.message}}")
    assert error

@pytest.mark.parametrize('route',['tables','gantt','rack','wafer','windows','carrier','process'])
def test_shared_loading_empty_error_contract(page,route):
    open_page(page,route)
    page.locator('[data-view-state]').select_option('loading')
    expect(page.locator('.engineering-widget')).to_contain_text('Loading this example')
    page.locator('[data-view-state]').select_option('empty')
    expect(page.locator('.engineering-widget')).to_contain_text('No records yet')
    page.locator('[data-view-state]').select_option('error')
    expect(page.locator('.engineering-widget')).to_contain_text('Data could not be loaded')
    page.get_by_role('button',name='Retry example').click()
    expect(page.locator('.engineering-widget .widget-state')).to_have_count(0)

def test_table_search_filter_sort_selection_archive(page):
    open_page(page,'tables')
    page.get_by_label('Search records').fill('calibration')
    expect(page.locator('tbody tr')).to_have_count(9)
    page.get_by_label('Search records').fill('')
    page.get_by_label('Filter status').select_option('Review')
    expect(page.locator('tbody')).to_contain_text('Review')
    page.get_by_label('Select current page',exact=True).check()
    expect(page.locator('.selection-bar')).to_contain_text('12 selected')
    page.get_by_role('button',name='Archive selected').click()
    assert sum(r['status']=='Archived' for r in model(page,'rf-record-table'))==12
    page.get_by_label('Filter status').select_option('All statuses')
    page.get_by_role('button',name='Group',exact=False).filter(has_text='Group').first.click()
    assert page.locator('.group-row').count()>0
    page.locator('[data-sort="title"]').click()
    expect(page.locator('th[aria-sort="ascending"]')).to_contain_text('Work item')

def test_table_page_scopes_bulk_selection(page):
    open_page(page,'tables')
    page.get_by_label('Select current page',exact=True).check()
    page.get_by_label('Next page',exact=True).click()
    expect(page.locator('.selection-bar')).to_have_count(0)
    expect(page.locator('tbody tr').first).to_contain_text('WK-0013')

def test_table_external_text_is_escaped(page):
    open_page(page,'tables')
    page.locator('rf-record-table').evaluate('''el=>{
        const v=el.model;v[0].title='<img src=x onerror="window.__xss=true">';el.configure(v);
    }''')
    expect(page.locator('.data-table')).to_contain_text('<img src=x')
    assert page.locator('.data-table img').count()==0
    assert page.evaluate('window.__xss===undefined')

def test_board_keyboard_equivalent_and_readonly(page):
    open_page(page,'boards')
    page.get_by_label('Move WK-0001',exact=True).select_option('Done')
    assert next(r for r in model(page,'rf-work-board') if r['id']=='WK-0001')['status']=='Done'
    page.locator('[data-view-state]').select_option('readonly')
    expect(page.get_by_label('Move WK-0001',exact=True)).to_be_disabled()

def test_gantt_rejects_overlap_and_applies_safe_dates(page):
    open_page(page,'gantt')
    original=model(page,'rf-gantt')
    page.locator('input[name="start"]').fill('7')
    page.get_by_role('button',name='Apply dates').click()
    expect(page.locator('[data-widget-alert]')).to_contain_text('overlaps prerequisite')
    assert model(page,'rf-gantt')==original
    page.locator('input[name="start"]').fill('10')
    page.get_by_role('button',name='Apply dates').click()
    assert next(t for t in model(page,'rf-gantt') if t['id']=='T3')['start']==9
    assert page.locator('.gantt-days>span').count()==30

def test_rack_rejects_collision_and_moves(page):
    open_page(page,'rack')
    inp=page.locator('rf-rack input[type="number"]').first
    inp.fill('24');page.locator('rf-rack form button').click()
    expect(page.locator('[data-widget-alert]')).to_contain_text('Collision')
    inp.fill('30');page.locator('rf-rack form button').click()
    assert next(d for d in model(page,'rf-rack') if d['id']=='D3')['start']==30
    page.get_by_role('button',name='Rear',exact=True).click()
    expect(page.locator('.rack-frame footer')).to_contain_text('rear')

def test_wafer_filter_keyboard_and_details(page):
    open_page(page,'wafer')
    assert page.locator('.die').count()==441
    first=page.locator('.die[tabindex="0"]');first.focus();before=first.get_attribute('data-die')
    page.keyboard.press('ArrowRight')
    assert page.evaluate('document.activeElement.getAttribute("data-die")')!=before
    page.keyboard.press('Enter')
    expect(page.get_by_role('dialog')).to_be_visible()
    page.get_by_label('Close inspector').click()

def test_calendar_add_and_month_boundary(page):
    open_page(page,'calendar')
    initial=len(model(page,'rf-calendar'))
    page.locator('input[name="title"]').fill('Review checkpoint')
    page.get_by_role('button',name='Add event').click()
    assert len(model(page,'rf-calendar'))==initial+1
    expect(page.locator('.calendar-days')).to_contain_text('Review checkpoint')
    page.get_by_label('Next month').click()
    expect(page.locator('rf-calendar h3').first).to_have_text('October 2026')

def test_windows_dirty_escape_focus_and_wizard_draft(page):
    open_page(page,'windows')
    page.locator('[data-window="dialog"]').click()
    page.locator('dialog input').fill('Unsaved work')
    page.keyboard.press('Escape')
    expect(page.locator('dialog')).to_be_visible()
    expect(page.locator('.discard-guard')).to_contain_text('Discard unsaved changes')
    page.get_by_role('button',name='Keep editing').click()
    expect(page.locator('dialog input')).to_be_focused()
    page.keyboard.press('Escape');page.get_by_role('button',name='Discard changes').click()
    expect(page.locator('dialog')).to_have_count(0)
    expect(page.locator('[data-window="dialog"]')).to_be_focused()
    page.locator('[data-window="wizard"]').click()
    page.locator('dialog input').fill('Qualification')
    page.get_by_role('button',name='Continue',exact=True).click()
    page.get_by_role('button',name='Back',exact=True).click()
    expect(page.locator('dialog input')).to_have_value('Qualification')
    page.get_by_role('button',name='Continue',exact=True).click()
    page.get_by_role('button',name='Continue',exact=True).click()
    page.get_by_role('button',name='Save example',exact=True).click()
    expect(page.locator('dialog')).to_have_count(0)

def test_all_window_types_close_and_trap_focus(page):
    open_page(page,'windows')
    for kind in ['dialog','drawer','sheet','fullscreen','wizard','confirm']:
        page.locator(f'[data-window="{kind}"]').click()
        expect(page.locator('dialog')).to_be_visible()
        for _ in range(12):
            page.keyboard.press('Tab')
            assert page.evaluate('document.querySelector("dialog").contains(document.activeElement)')
        page.keyboard.press('Escape')
        expect(page.locator('dialog')).to_have_count(0)

def test_theme_switch_preserves_unsaved_input(page):
    open_page(page,'forms')
    page.locator('input[name="name"]').fill('Do not lose this draft')
    page.locator('[data-theme-toggle]').click()
    expect(page.locator('input[name="name"]')).to_have_value('Do not lose this draft')
    expect(page.locator('html')).to_have_attribute('data-theme','dark')

def test_carrier_reassignment_retains_uniqueness(page):
    open_page(page,'carrier')
    page.get_by_label('Destination carrier slot').select_option('1')
    page.get_by_role('button',name='Reassign example').click()
    slots=model(page,'rf-carrier')
    assert next(s for s in slots if s['slot']==8)['waferId'] is None
    assert next(s for s in slots if s['slot']==1)['waferId']=='W-0107'

def test_traveler_rejects_skipping_and_completes_step(page):
    open_page(page,'traveler')
    page.locator('[data-step="S4"]').click()
    page.locator('[data-transition="running"]').click()
    expect(page.locator('[data-widget-alert]')).to_contain_text('prerequisite')
    page.locator('[data-step="S3"]').click()
    page.locator('[data-transition="complete"]').click()
    assert next(s for s in model(page,'rf-lot-traveler') if s['id']=='S3')['status']=='complete'

def test_notifications_and_permission_readonly(page):
    open_page(page,'notifications')
    page.get_by_role('button',name='Mark all read').click()
    assert all(n['read'] for n in model(page,'rf-notifications'))
    page.locator('[data-unread]').check()
    expect(page.locator('rf-notifications')).to_contain_text('You are all caught up')
    page.evaluate("window.location.hash='/permissions'")
    page.locator('[data-view-state]').select_option('readonly')
    for checkbox in page.locator('rf-permission-matrix input').all():expect(checkbox).to_be_disabled()

def test_split_keyboard_resize(page):
    open_page(page,'split')
    separator=page.get_by_role('separator',name='Resize sidebar')
    separator.focus();page.keyboard.press('ArrowRight')
    expect(separator).to_have_attribute('aria-valuenow','38')
    page.keyboard.press('Home');expect(separator).to_have_attribute('aria-valuenow','20')
    page.keyboard.press('End');expect(separator).to_have_attribute('aria-valuenow','65')

def test_json_validates_without_execution(page):
    open_page(page,'json')
    page.get_by_label('JSON configuration',exact=True).fill('not json')
    page.get_by_role('button',name='Validate & format').click()
    assert page.locator('[data-widget-alert]').inner_text()
    page.get_by_label('JSON configuration',exact=True).fill('{"name":"<script>window.__xss=true</script>"}')
    page.get_by_role('button',name='Validate & format').click()
    assert model(page,'rf-json-inspector')['name'].startswith('<script>')
    assert page.evaluate('window.__xss===undefined')

def test_command_palette_and_tab_keyboard(page):
    open_page(page,'tables')
    page.keyboard.press('Control+k')
    expect(page.get_by_role('dialog')).to_be_visible()
    page.locator('dialog input').fill('wafer')
    page.locator('dialog [data-result]').first.click()
    expect(page.locator('rf-wafer')).to_be_visible()
    page.locator('[data-tab="preview"]').focus();page.keyboard.press('ArrowRight')
    expect(page.locator('[data-tab="usage"]')).to_have_attribute('aria-selected','true')

@pytest.mark.parametrize('route',['overview','tables','windows','wafer','rack','gantt','carrier','floorplan','themes'])
def test_mobile_page_has_no_document_overflow(page,route):
    page.set_viewport_size({'width':375,'height':900})
    open_page(page,route)
    widths=page.evaluate('({scroll:document.documentElement.scrollWidth,viewport:window.innerWidth})')
    assert widths['scroll']<=widths['viewport']+1,widths

@pytest.mark.parametrize('route',['overview','gantt','rack','wafer','windows','carrier','floorplan','themes'])
@pytest.mark.parametrize('theme',['light','dark'])
def test_visual_evidence(page,route,theme):
    open_page(page,route,theme)
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(EVIDENCE/f'{route}-{theme}.png'),full_page=True,animations='disabled')

def test_custom_presentation_without_kernel_changes(page):
    open_page(page,'rack')
    page.locator('rf-rack').evaluate('''el=>el.configure([{id:'custom',name:'Local server',start:1,units:2,watts:100,status:'healthy'}],{presentation:{rack:{label:'My 24U cabinet',units:24,maxWatts:1000}}})''')
    expect(page.locator('.rack-frame header')).to_contain_text('My 24U cabinet')
    assert page.locator('.rack-unit').count()==24
    page.get_by_label('Starting rack unit').fill('3')
    page.get_by_role('button',name='Move equipment').click()
    assert model(page,'rf-rack')[0]['start']==3
    page.evaluate("location.hash='/gantt'")
    page.locator('rf-gantt').evaluate('''el=>el.configure([{id:'new',name:'New project',start:0,duration:3,progress:0,owner:'Team',dependencies:[]}],{presentation:{schedule:{startDate:'2027-01-01',days:31}}})''')
    expect(page.locator('rf-gantt')).to_contain_text('January 2027')
    assert page.locator('.gantt-days>span').count()==31

def test_two_topologies_do_not_duplicate_svg_ids(page):
    open_page(page,'topology')
    page.locator('rf-topology').evaluate('''el=>{const second=document.createElement('rf-topology');second.configure(el.model);el.after(second)}''')
    ids=page.locator('rf-topology [id]').evaluate_all('nodes=>nodes.map(n=>n.id)')
    assert len(ids)==len(set(ids))


def test_wafer_labels_match_screen_coordinate_orientation(page):
    open_page(page,'wafer')
    expect(page.locator('.wafer-svg')).to_contain_text('Y− (up)')
    expect(page.locator('rf-wafer')).to_contain_text('positive Y is down')

def test_trace_status_uses_external_model_instead_of_success_constant(page):
    open_page(page,'traces')
    page.locator('rf-trace-waterfall').evaluate("el=>{const model=el.model;model[0].status='error';el.configure(model)}")
    expect(page.locator('rf-trace-waterfall .component-toolbar')).to_contain_text('Contains errors')
