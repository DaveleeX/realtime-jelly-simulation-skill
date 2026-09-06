import * as THREE from 'three/webgpu';
import { texture, positionWorld, float, vec3, mx_noise_float, mix } from 'three/tsl';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import type { RefractiveLightField } from './refractive-light.js';

export async function makeTable(optics:RefractiveLightField,light:{color:THREE.Color;windowFraction:number;irradiance:number}) {
  const opticalUV=positionWorld.xz.sub(optics.originNode).div(optics.spanNode);
  const inside=float(opticalUV.x.greaterThan(0).and(opticalUV.x.lessThan(1)).and(opticalUV.y.greaterThan(0)).and(opticalUV.y.lessThan(1)));
  const shadowUV=positionWorld.xz.sub(optics.shadowOriginNode).div(optics.shadowSpanNode);
  const shadowInside=float(shadowUV.x.greaterThan(0).and(shadowUV.x.lessThan(1)).and(shadowUV.y.greaterThan(0)).and(shadowUV.y.lessThan(1)));
  const shadow=texture(optics.shadowTexture,shadowUV).r.mul(shadowInside);
  const contactUV=positionWorld.xz.sub(optics.contactOriginNode).div(optics.shadowSpanNode);
  const contactInside=float(contactUV.x.greaterThan(0).and(contactUV.x.lessThan(1)).and(contactUV.y.greaterThan(0)).and(contactUV.y.lessThan(1)));
  const contact=texture(optics.shadowTexture,contactUV).g.mul(contactInside);
  const broad=mx_noise_float(positionWorld.mul(vec3(3,3,8)));
  const grain=mx_noise_float(positionWorld.mul(850)).mul(.5).add(.5);
  const veins=mx_noise_float(positionWorld.mul(vec3(12,8,28)).add(broad.mul(3))).abs().smoothstep(.01,.035).oneMinus();
  const albedo=mix(vec3(.032,.038,.043),vec3(.115,.125,.13),veins.mul(.34)).mul(grain.mul(.14).add(.93));
  const material=new THREE.MeshPhysicalNodeMaterial({metalness:0,roughness:.29,clearcoat:.24,clearcoatRoughness:.22});
  material.roughnessNode=grain.mul(.09).add(.25);
  material.colorNode=albedo.mul(float(1).sub(shadow.mul(light.windowFraction))).mul(float(1).sub(contact.mul(.5)));
  material.emissiveNode=albedo.mul(texture(optics.lightTexture,opticalUV).rgb).mul(light.irradiance/Math.PI).mul(vec3(light.color.r,light.color.g,light.color.b)).mul(inside);
  const mesh=new THREE.Group();
  const geometries:THREE.BufferGeometry[]=[];
  const addBox=(x:number,y:number,z:number,px:number,py:number,pz:number,r=.001)=>{
    const geometry=new RoundedBoxGeometry(x,y,z,2,r);geometries.push(geometry);
    const part=new THREE.Mesh(geometry,material);part.position.set(px,py,pz);mesh.add(part);
  };
  // Honed stone slab, 32 mm thick. Its flat top matches the physics floor exactly.
  addBox(2.4,.032,.85,0,-.016,0,.004);
  return {mesh,dispose:()=>{geometries.forEach(g=>g.dispose());material.dispose();}};
}
