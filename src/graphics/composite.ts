import { RenderPipeline, Vector3 } from 'three/webgpu';
import type { WebGPURenderer, Scene, PerspectiveCamera } from 'three/webgpu';
import { pass, screenUV, float, vec3, vec4, uniform, convertToTexture } from 'three/tsl';
import { bloom } from 'three/addons/tsl/display/BloomNode.js';
import { dof } from 'three/addons/tsl/display/DepthOfFieldNode.js';

/** Linear HDR scene → restrained lens glow → grade → one AgX/output transform. */
export function createComposite(renderer:WebGPURenderer,scene:Scene,camera:PerspectiveCamera,subject:Vector3) {
  const scenePass=pass(scene,camera);
  const focus=uniform(.2);
  const focusPoint=new Vector3();
  const depth=scenePass.getViewZNode();
  // Keep a 5 cm focus envelope around the subject before defocus begins.
  const adjustedDepth=depth.negate().sub(focus).abs().sub(.025).max(0).add(focus).negate();
  const lens=dof(scenePass.getTextureNode('output'),adjustedDepth,focus,.075,2.2);
  const color=convertToTexture(lens);
  const glow=bloom(color,.075,.18,1.6);
  const vignette=screenUV.sub(.5).length().smoothstep(.24,.73).mul(.065);
  const graded=color.rgb.add(glow.rgb).mul(vec3(.985,1.01,1.015)).mul(float(1).sub(vignette));
  const pipeline=new RenderPipeline(renderer,vec4(graded,color.a));
  return {render:()=>{camera.updateMatrixWorld();focus.value=Math.max(.01,-focusPoint.copy(subject).applyMatrix4(camera.matrixWorldInverse).z);pipeline.render();},dispose:()=>{lens.dispose();glow.dispose();scenePass.dispose();pipeline.dispose();}};
}
