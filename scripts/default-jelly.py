"""Generate an original, watertight high-density gummy mascot for model switching."""
import json,struct
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage.measure import marching_cubes
S=.022; origin=np.array([-1.55,-.08,-.82],np.float32); end=np.array([1.55,5.45,.92],np.float32)
a=[np.arange(x,y,S,dtype=np.float32) for x,y in zip(origin,end)];X,Y,Z=np.meshgrid(*a,indexing='ij',sparse=True);F=np.full(tuple(map(len,a)),8,np.float32)
def union(d,k=.12):
 global F
 h=np.maximum(k-np.abs(F-d),0)/k;F=np.minimum(F,d)-h*h*k*.25
def ell(c,r,k=.12,cut=False):
 global F
 x=X-c[0];y=Y-c[1];z=Z-c[2];q=np.sqrt((x/r[0])**2+(y/r[1])**2+(z/r[2])**2);q1=np.sqrt((x/r[0]**2)**2+(y/r[1]**2)**2+(z/r[2]**2)**2);d=q*(q-1)/np.maximum(q1,1e-7)
 if cut:F=np.maximum(F,-d)
 else:union(d,k)
def cap(a,b,r,rb=None,k=.12):
 a=np.array(a);b=np.array(b);v=b-a;t=np.clip(((X-a[0])*v[0]+(Y-a[1])*v[1]+(Z-a[2])*v[2])/np.dot(v,v),0,1);rr=r if rb is None else r+(rb-r)*t;union(np.sqrt((X-a[0]-t*v[0])**2+(Y-a[1]-t*v[1])**2+(Z-a[2]-t*v[2])**2)-rr,k)
# Original gummy mascot: round head, tapered torso, open arms and planted legs.
ell([0,3.95,0],[.91,1.03,.69],.16);ell([0,2.63,0],[.70,1.0,.51],.22)
cap([-.50,3.05,0],[-1.13,2.42,.04],.32,.24,.16);ell([-1.18,2.34,.05],[.31,.35,.28],.11)
cap([[.50,3.05,0][0],3.05,0],[1.13,2.42,.04],.32,.24,.16);ell([1.18,2.34,.05],[.31,.35,.28],.11)
cap([-.28,1.86,0],[-.48,.62,.08],.32,.25,.18);ell([-.55,.30,.24],[.38,.31,.48],.12)
cap([[.28,1.86,0][0],1.86,0],[.48,.62,.08],.32,.25,.18);ell([.55,.30,.24],[.38,.31,.48],.12)
# Molded face: inset sockets, raised eyes, happy mouth and tiny nose.
for x in [-.33,.33]:
 ell([x,4.10,.622],[.215,.27,.11],cut=True);ell([x,4.09,.618],[.145,.19,.09],.035);ell([x+.02,4.07,.682],[.065,.10,.045],.025)
ell([0,3.84,.69],[.11,.10,.08],.045);ell([0,3.59,.658],[.30,.16,.12],cut=True);ell([.04,3.52,.605],[.16,.07,.06],.025)
# Small gummy crest creates a distinctive default silhouette.
ell([0,4.91,0],[.31,.21,.31],.10);ell([0,5.05,0],[.16,.23,.17],.08)
F=gaussian_filter(F,.5);v,f,_,_=marching_cubes(F,0,spacing=(S,S,S),allow_degenerate=False);v+=origin
vol=np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()/6
if vol<0:f=f[:,[0,2,1]]
edges=np.sort(np.vstack([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),1);_,cnt=np.unique(edges,axis=0,return_counts=True)
out=Path(__file__).resolve().parents[1]/'dist'
with open(out/'default-jelly.bin','wb') as q:q.write(struct.pack('<II',len(v),len(f)*3));q.write(v.astype('<f4').tobytes());q.write(f.astype('<u4').tobytes())
meta={'vertices':len(v),'triangles':len(f),'boundary_edges':int((cnt==1).sum()),'nonmanifold_edges':int((cnt>2).sum()),'voxel_size':S};(out/'default-jelly-info.json').write_text(json.dumps(meta,indent=2));print(meta)
