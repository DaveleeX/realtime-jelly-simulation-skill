import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {parseBabyCage} from '../src/physics/baby-cage.ts';
import {SoftBody} from '../src/physics/soft-body.js';
import {PHYS} from '../src/physics/constants.js';
import {Locomotion} from '../src/game/locomotion.ts';
const data=readFileSync('src/assets/model/wukong.bin');
const manifest=JSON.parse(readFileSync('src/assets/model/wukong.json','utf8'));
const cage=parseBabyCage(data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength),manifest);
const body=new SoftBody(cage);
const rig=new Locomotion(body);
for(let i=0;i<480;i++){rig.step(PHYS.step);body.step(PHYS.step);rig.afterStep();}
body.updateSurface();
assert(body.isFinite(),'Wukong stays finite after gravity settling');
assert(body.volumeRatio()>.8&&body.volumeRatio()<1.2,'Wukong preserves volume');
assert(body.lastMinJacobian>.12,'Cage keeps its orientation');
assert(body.surface.geometry.boundingBox.min.y>-.002,'Wukong does not pass through the counter');
assert(body.surface.geometry.boundingBox.max.y>.05,'Wukong retains its upright silhouette');
console.log({volume:body.volumeRatio(),minJacobian:body.lastMinJacobian,bounds:body.surface.geometry.boundingBox});
