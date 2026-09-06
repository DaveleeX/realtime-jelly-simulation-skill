import './style.css';

document.querySelector<HTMLDivElement>('#app')!.innerHTML=`
  <main id="viewport" aria-label="Jelly baby playground"></main>
  <nav class="model-switch" role="group" aria-label="切换果冻形态">
      <button type="button" data-model="default">默认果冻</button>
      <button type="button" data-model="wukong">孙悟空</button>
  </nav>
  <section id="loading" role="status" aria-live="polite"><div class="loading-card"><div class="jelly-mark"></div><h2>A little life.</h2><p id="load-message">Warming up the world</p><pre id="fatal" hidden></pre><button id="retry" hidden>Try again</button></div></section>
`;

let selectedModel=new URLSearchParams(location.search).get('model')==='wukong'?'wukong':'default';
type ModelName='default'|'wukong';
type Game={stop:()=>void;switchModel:(model:ModelName)=>Promise<void>};
let game:Game|undefined;
document.querySelectorAll<HTMLButtonElement>('[data-model]').forEach(button=>{
  const active=button.dataset.model===selectedModel;
  button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));button.disabled=true;
  button.addEventListener('click',async()=>{
    const next=button.dataset.model as ModelName;
    if(next===selectedModel||!game)return;
    const buttons=[...document.querySelectorAll<HTMLButtonElement>('[data-model]')];
    buttons.forEach(item=>item.disabled=true);document.documentElement.classList.add('model-changing');
    try {
      await game.switchModel(next);selectedModel=next;
      buttons.forEach(item=>{const active=item.dataset.model===next;item.classList.toggle('active',active);item.setAttribute('aria-pressed',String(active));});
      const url=new URL(location.href);if(next==='wukong')url.searchParams.set('model','wukong');else url.searchParams.delete('model');history.replaceState(null,'',url);
    } catch(error){fail(error);} finally {buttons.forEach(item=>item.disabled=false);document.documentElement.classList.remove('model-changing');}
  });
});

let stage='Loading the game',failed=false;
function fail(reason:unknown) {
  if(failed)return;failed=true;game?.stop();
  const error=reason instanceof Error?reason:new Error(String(reason));
  document.querySelector('#loading')!.classList.remove('hidden');
  document.querySelector('#loading')!.classList.add('failed');
  document.querySelector('h2')!.textContent='A little hiccup.';
  document.querySelector('#load-message')!.textContent='The game couldn’t start. Details below.';
  const fatal=document.querySelector<HTMLPreElement>('#fatal')!;fatal.hidden=false;
  fatal.textContent=`${stage}\n${error.message}\n\nViewport: ${innerWidth} × ${innerHeight} · DPR ${devicePixelRatio}\n${navigator.userAgent}`;
  document.querySelector<HTMLButtonElement>('#retry')!.hidden=false;
  console.error(`[Jelly Baby / ${stage}]`,error);
}
window.addEventListener('error',event=>fail(event.error||event.message));
window.addEventListener('unhandledrejection',event=>fail(event.reason));
document.querySelector('#retry')!.addEventListener('click',()=>location.reload());

// One observed chain covers imports, initialization, compilation, warmup and first render.
void import('./game/runtime.ts').then(({startGame})=>startGame(message=>{
  if(failed)throw new Error('Startup aborted after a GPU failure');
  stage=message;document.querySelector('#load-message')!.textContent=message;
},fail)).then(started=>{
  game=started;
  if(failed){game.stop();return;}
  stage='Playing';document.querySelector('#loading')!.classList.add('hidden');
  document.querySelectorAll<HTMLButtonElement>('[data-model]').forEach(button=>button.disabled=false);
}).catch(fail);
