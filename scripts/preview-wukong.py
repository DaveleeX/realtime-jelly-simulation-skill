"""Offline clay preview of the generated surface for sculpt review."""
import struct
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
root=Path(__file__).resolve().parents[1]
b=(root/'dist/wukong-sculpt.bin').read_bytes()
nv,ni=struct.unpack_from('<II',b)
v=np.frombuffer(b,'<f4',nv*3,8).reshape(-1,3)
f=np.frombuffer(b,'<u4',ni,8+nv*12).reshape(-1,3)
t=v[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-9)
light=np.array([-.4,.65,1]);light/=np.linalg.norm(light)
shade=.35+.6*np.maximum(0,n@light)
colors=np.stack([shade*.92,shade*.94,shade],axis=1)
fig=plt.figure(figsize=(8,10),facecolor='#eeeeef');ax=fig.add_subplot(projection='3d')
ax.add_collection3d(Poly3DCollection(t[:,:,[0,2,1]],facecolors=colors,edgecolors='none',rasterized=True))
ax.set(xlim=(-2.4,2),ylim=(-1.3,1.4),zlim=(0,6.5));ax.set_box_aspect((4.4,2.7,6.5));ax.view_init(elev=8,azim=72)
ax.set_axis_off();ax.set_facecolor('#eeeeef');plt.tight_layout()
fig.savefig('/workspace/scratch/b3518686c926/wukong-clay-review.png',dpi=150,bbox_inches='tight')
