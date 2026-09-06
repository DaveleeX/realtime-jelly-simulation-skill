import * as THREE from 'three/webgpu';
import { SoftBody } from '../physics/soft-body.js';
import { PHYS } from '../physics/constants.js';
import { loadBabyCage, type JellyModelName } from '../physics/baby-cage.ts';
import { RefractiveLightField } from '../graphics/refractive-light.js';
import { Baby, ABSORPTION } from '../graphics/baby.ts';
import { loadEnvironment } from '../graphics/environment.ts';
import { makeTable } from '../graphics/table.ts';
import { Locomotion } from './locomotion.ts';
import { Input } from './input.ts';
import { JellySound } from './sound.ts';
import { createRenderer, resizeView } from '../graphics/renderer.ts';
import { OpticalTransport } from '../graphics/transport.ts';
import { createComposite } from '../graphics/composite.ts';
import { FixedStepper } from './fixed-step.ts';

export async function startGame(stage:(s:string)=>void,fail:(e:unknown)=>void) {
  const initialModel=(new URLSearchParams(location.search).get('model')==='wukong'?'wukong':'default') as JellyModelName;
  stage('Starting WebGPU');
  const renderer=await createRenderer(fail);
  document.querySelector('#viewport')!.appendChild(renderer.domElement);
  const sound=new JellySound();
  const scene=new THREE.Scene();
  const camera=new THREE.PerspectiveCamera(36,1,.001,40);camera.position.set(.082,.126,.19);
  stage('Reading the light');
  const environment=await loadEnvironment(renderer,scene);
  // Rembrandt-style three-quarter key, restrained cool fill and warm edge light.
  const key=new THREE.DirectionalLight(0xffd5b5,3.8);key.position.set(-.28,.42,.26);
  const fill=new THREE.DirectionalLight(0x9fbce8,1.05);fill.position.set(.30,.16,.22);
  const rim=new THREE.DirectionalLight(0xff9f62,1.65);rim.position.set(.18,.27,-.30);
  const ambient=new THREE.HemisphereLight(0xb9cdf4,0x291712,.42);
  scene.add(key,fill,rim,ambient);

  // Start both downloads immediately; switching never reloads the page or waits on the network.
  const cageCache=new Map<JellyModelName,ReturnType<typeof loadBabyCage>>([
    ['default',loadBabyCage('default')],['wukong',loadBabyCage('wukong')],
  ]);
  const takeCage=(model:JellyModelName)=>{
    const cached=cageCache.get(model)??loadBabyCage(model);
    cageCache.delete(model);return cached;
  };
  const createWorld=async(model:JellyModelName)=>{
    const body=new SoftBody(await takeCage(model));
    const baby=new Baby(body,model==='default');scene.add(baby.group);
    const optics=new RefractiveLightField(body.cage.opticalSurface,environment.incoming,ABSORPTION);
    const table=await makeTable(optics,environment);scene.add(table.mesh);
    const rig=new Locomotion(body);rig.onContact=(speed,foot)=>sound.contact(speed,foot);
    const physicsClock=new FixedStepper(PHYS.step);
    let input!:Input;
    const reset=()=>{input.recenter();body.reset();baby.resetFace();physicsClock.reset();};
    input=new Input(camera,renderer.domElement,body,baby.mesh,rig,sound,reset);
    const transport=new OpticalTransport(optics,body,camera,environment.incoming,fail);
    const composite=createComposite(renderer,scene,camera,body.center);
    for(let i=0;i<80;i++){rig.step(PHYS.step);body.step(PHYS.step);}
    body.updateSurface();baby.update();input.update(1);optics.update(renderer,body,true);await transport.update();
    return {model,body,baby,optics,table,rig,physicsClock,input,transport,composite};
  };
  const destroyWorld=(world:Awaited<ReturnType<typeof createWorld>>)=>{
    world.input.dispose();world.transport.dispose();world.composite.dispose();
    scene.remove(world.baby.group,world.table.mesh);world.baby.dispose();world.table.dispose();world.optics.dispose();
  };

  stage('Making a little jelly');let world=await createWorld(initialModel);
  const resize=()=>resizeView(renderer,camera,world.input.controls);
  let resizeFrame=0;
  const resizeObserver=new ResizeObserver(()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(resize);});
  resizeObserver.observe(document.querySelector('#viewport')!);resize();
  stage('Compiling the material');await renderer.compileAsync(scene,camera);
  stage('Drawing the first frame');world.composite.render();
  const backend=renderer.backend as unknown as {device:GPUDevice};await backend.device.queue.onSubmittedWorkDone();
  let lastTime=performance.now(),disposed=false,swapping=false;
  const frame=(time:number)=>{
    if(disposed||swapping)return;
    try {
      const dt=Math.min(.05,Math.max(0,(time-lastTime)/1000));lastTime=time;
      if(document.hidden){world.physicsClock.reset();return;}
      const steps=world.physicsClock.advance(dt,()=>{
        world.input.step(PHYS.step);world.rig.step(PHYS.step);world.body.step(PHYS.step);world.input.afterPhysicsStep();world.rig.afterStep();
      });
      if(steps&&world.body.surfaceDirty){if(!world.body.isFinite())throw new Error('The soft-body simulation produced an invalid state');world.body.updateSurface();}
      world.baby.update(dt);world.input.update(dt);world.transport.follow();world.optics.update(renderer,world.body);
      void world.transport.update().catch(fail);world.composite.render();
    } catch(error){fail(error);}
  };
  await renderer.setAnimationLoop(frame);
  const switchModel=async(model:JellyModelName)=>{
    if(disposed||swapping||model===world.model)return;
    swapping=true;world.input.clear();
    try {
      const previous=world;const next=await createWorld(model);
      resizeView(renderer,camera,next.input.controls);await renderer.compileAsync(scene,camera);
      previous.baby.group.visible=false;previous.table.mesh.visible=false;
      next.composite.render();await backend.device.queue.onSubmittedWorkDone();
      world=next;destroyWorld(previous);lastTime=performance.now();
      // Prime a fresh parsed cage for the next return switch while the new model is already visible.
      cageCache.set(previous.model,loadBabyCage(previous.model));
    } finally {swapping=false;}
  };
  const dispose=()=>{
    if(disposed)return;disposed=true;void renderer.setAnimationLoop(null);destroyWorld(world);sound.dispose();resizeObserver.disconnect();cancelAnimationFrame(resizeFrame);
    environment.dispose();renderer.dispose();
  };
  window.addEventListener('pagehide',event=>{if(!event.persisted)dispose();});
  if(import.meta.hot)import.meta.hot.dispose(dispose);
  return {stop:dispose,switchModel};
}
