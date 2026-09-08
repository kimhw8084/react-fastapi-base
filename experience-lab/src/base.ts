import {validatePresentation,type WidgetPresentation} from './presentation.js';
import {validateWidgetModel} from './validation.js';
import {escapeHtml as h,type ViewState} from './model.js';
export interface WidgetOptions {state?:ViewState;readonly?:boolean;presentation?:WidgetPresentation;}
/** Light DOM preserves one token/stylesheet/accessibility contract across React and the lab. */
export abstract class EngineeringElement<T> extends HTMLElement {
 protected value:T;
 protected options:WidgetOptions={};
 protected initialized=false;
 private error='';
 protected constructor(initial:T){super();this.value=structuredClone(initial);}
 configure(value:T,options:WidgetOptions={}):void{validateWidgetModel(this.localName,value);validatePresentation(options.presentation);if(options.state&&!['ready','loading','empty','error','readonly'].includes(options.state))throw new TypeError('Invalid widget state.');this.value=structuredClone(value);this.options=structuredClone(options);if(this.initialized)this.render();}
 get model():T{return structuredClone(this.value);}
 connectedCallback():void{this.initialized=true;this.classList.add('engineering-widget');this.render();}
 protected get readonlyMode():boolean{return this.options.readonly===true||this.options.state==='readonly';}
 protected change(value:T,reason:string):void{if(this.readonlyMode)return;validateWidgetModel(this.localName,value);this.value=value;this.error='';this.dispatchEvent(new CustomEvent('model-change',{detail:{value:structuredClone(value),reason},bubbles:true}));this.render();}
 protected select(detail:unknown):void{this.dispatchEvent(new CustomEvent('record-select',{detail,bubbles:true}));}
 protected fail(message:string):void{this.error=message;const el=this.querySelector<HTMLElement>('[data-widget-alert]');if(el)el.textContent=message;}
 protected frame(content:string):void{
  const state=this.options.state??'ready';
  if(state==='loading'){this.innerHTML='<div class="widget-state" role="status"><div class="skeleton-bar"></div><div class="skeleton-bar short"></div><p>Loading this example…</p></div>';return;}
  if(state==='empty'){this.innerHTML='<div class="widget-state"><span class="state-symbol" aria-hidden="true">◫</span><h3>No records yet</h3><p>The component preserves its layout when there is no data.</p></div>';return;}
  if(state==='error'){this.innerHTML='<div class="widget-state" role="alert"><span class="state-symbol" aria-hidden="true">!</span><h3>Data could not be loaded</h3><p>Example failure state. Your existing records have not changed.</p><button data-retry class="button">Retry example</button></div>';this.querySelector('[data-retry]')?.addEventListener('click',()=>{this.options={...this.options,state:'ready'};this.render();});return;}
  const active=document.activeElement instanceof HTMLInputElement&&this.contains(document.activeElement)?document.activeElement:null;
  const focus=active?.dataset.focus;const cursor=active?.selectionStart;
  this.innerHTML=`${this.readonlyMode?'<div class="readonly-note">Read-only preview · mutation controls disabled</div>':''}<div data-widget-alert role="alert" class="widget-alert">${h(this.error)}</div>${content}`;
  if(focus)queueMicrotask(()=>{const next=this.querySelector<HTMLInputElement>(`[data-focus="${focus}"]`);next?.focus();if(next&&cursor!==null&&cursor!==undefined)try{next.setSelectionRange(cursor,cursor);}catch{}});
 }
 protected on(selector:string,event:string,handler:(e:Event)=>void):void{this.querySelectorAll(selector).forEach(el=>el.addEventListener(event,handler));}
 protected input(selector:string):HTMLInputElement{return this.querySelector<HTMLInputElement>(selector)!;}
 abstract render():void;
}
export function register(name:string,component:CustomElementConstructor):void{if(!customElements.get(name))customElements.define(name,component);}
export const badge=(label:string,tone='neutral')=>`<span class="badge tone-${h(tone)}"><span class="badge-dot" aria-hidden="true"></span>${h(label)}</span>`;
export const sectionHeading=(eyebrow:string,title:string,description='')=>`<div class="section-heading"><div><span class="eyebrow">${h(eyebrow)}</span><h2>${h(title)}</h2>${description?`<p>${h(description)}</p>`:''}</div></div>`;
