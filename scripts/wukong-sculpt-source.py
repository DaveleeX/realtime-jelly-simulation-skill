"""Build a single watertight, smooth-union Monkey King jelly mold."""
import json,struct
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.ndimage import gaussian_filter
from skimage.measure import marching_cubes
STEP=.019
origin=np.array([-2.4,-.12,-1.25],np.float32)
end=np.array([1.95,6.45,1.4],np.float32)
axes=[np.arange(a,b,STEP,dtype=np.float32) for a,b in zip(origin,end)]
X,Y,Z=np.meshgrid(*axes,indexing='ij',sparse=True)
F=np.full(tuple(len(a) for a in axes),8,np.float32)
def union(d,k=.085):
 global F
 h=np.maximum(k-np.abs(F-d),0)/k
 F=np.minimum(F,d)-h*h*k*.25

def ell(c,r,k=.08,cut=False,angle=0):
 global F
 x=X-c[0]; y=Y-c[1];z=Z-c[2]
 if angle:x,y=x*np.cos(angle)+y*np.sin(angle),-x*np.sin(angle)+y*np.cos(angle)
 q=np.sqrt((x/r[0])**2+(y/r[1])**2+(z/r[2])**2)
 # Approximate signed ellipsoid distance with a stable gradient-length correction.
 q1=np.sqrt((x/(r[0]*r[0]))**2+(y/(r[1]*r[1]))**2+(z/(r[2]*r[2]))**2)
 d=q*(q-1)/np.maximum(q1,1e-8)
 if cut:F=np.maximum(F,-d)
 else:union(d,k)

def capsule(a,b,r,rb=None,k=.07,cut=False):
 global F
 a=np.array(a);b=np.array(b);v=b-a
 t=np.clip(((X-a[0])*v[0]+(Y-a[1])*v[1]+(Z-a[2])*v[2])/np.dot(v,v),0,1)
 d=np.sqrt((X-a[0]-t*v[0])**2+(Y-a[1]-t*v[1])**2+(Z-a[2]-t*v[2])**2)-(r if rb is None else r+(rb-r)*t)
 if cut:F=np.maximum(F,-d)
 else:union(d,k)

def curve(pts,r,k=.035,cut=False,n=22):
 p=np.array(pts);t=np.linspace(0,1,len(p));p=CubicSpline(t,p,axis=0)(np.linspace(0,1,n))
 for a,b in zip(p[:-1],p[1:]):capsule(a,b,r,k=k,cut=cut)

# Main volumes connect with broad anatomical transitions.
ell([-.04,2.6,0],[.59,.78,.39],k=.18,angle=.10)
ell([-.12,3.25,0],[.34,.39,.3],k=.18)
ell([-.18,4.12,0],[.94,.96,.72],k=.12)
# Temples, cheek ruff and ears retain a monkey silhouette.
for side in [-1,1]:
 x=-.18+side*.92
 ell([x,3.98,.085],[.255,.30,.205],k=.065,angle=-side*.12)
 ell([x+side*.016,4.015,.248],[.155,.19,.100],cut=True)
 curve([[x-side*.08,3.93,.18],[x-side*.07,4.04,.215],[x+side*.035,4.08,.214]],.041,k=.025,n=10)
 ell([-.18+side*.48,3.77,.25],[.36,.37,.43],k=.09)
# One integrated raised heart-shaped monkey facial mask.
ell([-.49,4.15,.59],[.415,.50,.23],k=.055,angle=-.15)
ell([.13,4.15,.59],[.415,.50,.23],k=.055,angle=.15)
ell([-.18,3.76,.57],[.61,.40,.335],k=.13)
# Eye recesses, smooth lids and raised pupils are embossed in the same material.
for x in [-.49,.13]:
 ell([x,4.18,.805],[.247,.295,.105],cut=True)
 ell([x,4.17,.801],[.193,.245,.144],k=.035)
 # Smooth recessed oval pupils, like the supplied clay figure; no protruding beads.
 ell([x-.041,4.165,.916],[.116,.180,.091],cut=True)
 # expressive eyebrows, fused into the forehead rather than separate strips
 ell([x-.005,4.54,.762],[.115,.048,.057],k=.025)
ell([-.18,3.985,.825],[.16,.103,.087],k=.095)
# Smile cavity plus fused tongue and a rounded top lip.
ell([-.13,3.615,.827],[.295,.202,.175],cut=True,angle=.14)
ell([-.075,3.491,.766],[.157,.076,.085],k=.032)
curve([[-.411,3.756,.805],[-.20,3.735,.881],[.15,3.80,.827]],.029,k=.015,n=18)
# Carved forehead hair and cheek tufts give the mold readable sculptural detail.
for side in [-1,1]:
 for j in range(3):
  x=-.18+side*(.61+j*.055)
  curve([[x,4.7-j*.12,.41],[x+side*.03,4.54-j*.12,.5],[x-side*.025,4.39-j*.12,.51]],.018,cut=True,n=8)
# Crown, ring bands and organically thickened double plumes.
ell([-.12,5.02,-.015],[.34,.16,.29],k=.085)
ell([-.12,5.19,-.015],[.25,.20,.215],k=.06)
for h,r in [(5.02,.34),(5.18,.255)]:
 pts=[[-.12+r*np.cos(a),h,-.015+r*.85*np.sin(a)] for a in np.linspace(0,2*np.pi,30)]
 for a,b in zip(pts[:-1],pts[1:]):capsule(a,b,.047,k=.02)
def plume(points):
 p=CubicSpline(np.linspace(0,1,len(points)),np.array(points),axis=0)(np.linspace(0,1,80))
 for i,c in enumerate(p):
  t=i/(len(p)-1); tangent=p[min(i+1,len(p)-1)]-p[max(i-1,0)]
  width=.067+.065*np.sin(np.pi*t)**.8
  ell(c,[width,.068,.043],k=.033,angle=np.arctan2(tangent[1],tangent[0])+np.pi/2)
plume([[-.29,5.26,0],[-.50,5.96,-.08],[-.16,6.16,-.20],[.39,5.84,-.32],[.51,5.18,-.39],[.37,4.78,-.45]])
plume([[.015,5.28,0],[.57,6.08,-.10],[1.15,6.12,-.24],[1.64,5.62,-.40],[1.48,4.91,-.53],[1.04,4.12,-.55],[.92,3.06,-.17]])
# Arms sweep out from the shoulder with tapered sleeves.
capsule([-.46,2.96,0],[-.94,2.86,.04],.29,.24,k=.16)
capsule([-.94,2.86,.04],[-1.29,2.55,.17],.25,.18,k=.12)
capsule([.39,2.96,0],[.96,2.77,-.005],.31,.24,k=.15)
capsule([.96,2.77,0],[1.35,2.40,.07],.24,.17,k=.11)
ell([-1.34,2.46,.18],[.23,.23,.22],k=.10)
ell([1.40,2.30,.08],[.21,.23,.2],k=.09)
for x in [-1.44,-1.35,-1.26]:capsule([x,2.33,.345],[x,2.5,.37],.044,k=.023)
for x in [1.3,1.39,1.48]:capsule([x,2.18,.225],[x,2.33,.248],.04,k=.02)
# Shoulder plates merge into cloth; all trim is molded relief.
ell([-.59,3.075,.01],[.35,.105,.30],k=.045,angle=.11)
ell([.56,3.075,0],[.36,.105,.3],k=.045,angle=-.19)
ell([-.02,3.04,.4],[.16,.17,.12],k=.06)
ell([-.25,3.08,.33],[.25,.135,.11],k=.055,angle=-.50)
ell([.21,3.04,.33],[.24,.135,.11],k=.055,angle=.58)
ell([.05,2.79,.42],[.14,.28,.065],k=.04,angle=.35)
curve([[-.37,2.99,.28],[-.24,2.68,.405],[.08,2.30,.40],[.23,2.10,.31]],.04,k=.038,n=18)
curve([[.38,2.99,.26],[.23,2.65,.41],[-.06,2.10,.375]],.039,k=.035,n=18)
ell([-.005,2.09,0],[.60,.145,.455],k=.08)
ell([-.01,2.10,.451],[.16,.091,.048],k=.025)
# Solid flared coat volume with a carved front opening. No open cylinder shells.
yc=np.clip((2.06-Y)/1.04,0,1)
rad=.48+yc*.31
rr=np.sqrt(((X-.11)/rad)**2+((Z+.05)/(rad*.72))**2)
side=(rr-1)*rad*.72
bottom=1.00+.10*np.sin((X-.1)*3)+.07*np.cos(Z*4)
coat=np.maximum(side,np.maximum(Y-2.08,bottom-Y))
union(coat,.10)
# Sweeping opening separates skirt from raised knee while retaining a solid back.
ell([-.51,1.27,.60],[.62,.52,.47],cut=True,angle=-.25)
curve([[-.10,2.03,.443],[.15,1.56,.53],[.39,1.08,.55]],.049,k=.03,n=18)
for x in [.48,.65]:curve([[x-.18,1.84,.39],[x,1.42,.47],[x+.04,1.13,.44]],.018,cut=True,n=12)
# Lifted leg and supporting leg, with connected boots.
capsule([-.25,1.78,.025],[-.71,1.42,.24],.26,.255,k=.12)
ell([-.71,1.41,.24],[.27,.26,.27],k=.075)
capsule([-.7,1.36,.21],[-.52,.89,.15],.195,.153,k=.075)
capsule([-.55,1.01,.15],[-.51,.73,.23],.198,.18,k=.04)
ell([-.59,.69,.35],[.22,.17,.35],k=.07,angle=-.17)
capsule([.31,1.46,-.08],[.61,.99,-.07],.25,.21,k=.14)
capsule([.61,1.0,-.07],[.86,.54,.06],.19,.155,k=.09)
capsule([.81,.66,.04],[.96,.30,.17],.20,.18,k=.04)
ell([.92,.205,.32],[.235,.18,.37],k=.08,angle=.13)
curve([[-.64,.96,.30],[-.66,.72,.59],[-.48,.66,.63]],.03,k=.022,n=12)
curve([[.95,.57,.25],[1.07,.3,.47],[.86,.19,.62]],.03,k=.022,n=12)
# Staff fuses directly into the grasp. Slightly stout for a cast-jelly silhouette.
a=np.array([-1.94,4.86,.17]);b=np.array([-.73,.53,.34]);d=(b-a)/np.linalg.norm(b-a)
capsule(a,b,.084,k=.055)
capsule(a,a+d*.63,.109,k=.03)
capsule(b,b-d*.58,.109,k=.03)
# Gentle surface polish; smaller than the facial relief.
F=gaussian_filter(F,.48)
verts,faces,normals,_=marching_cubes(F,0,spacing=(STEP,STEP,STEP),gradient_direction='ascent',allow_degenerate=False)
verts+=origin
# Enforce outward winding from signed volume.
volume=np.einsum('ij,ij->i',verts[faces[:,0]],np.cross(verts[faces[:,1]],verts[faces[:,2]])).sum()/6
if volume<0:faces=faces[:,[0,2,1]]
# Connected components reveal accidental floating details.
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
edges=np.vstack([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]])
A=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(len(verts),len(verts)))
n,labels=connected_components(A,directed=False)
counts=np.bincount(labels);keep=labels==np.argmax(counts)
print('components',n,'sizes',sorted(counts.tolist(),reverse=True)[:8])
if n>1:
 faces=faces[np.all(keep[faces],axis=1)];ids=np.full(len(verts),-1);ids[keep]=np.arange(keep.sum());faces=ids[faces];verts=verts[keep]
# Welded indexed binary format keeps load and memory predictable.
out=Path(__file__).resolve().parents[1]/'dist'
with open(out/'wukong-sculpt.bin','wb') as f:
 f.write(struct.pack('<II',len(verts),len(faces)*3));f.write(verts.astype('<f4').tobytes());f.write(faces.astype('<u4').tobytes())
edges=np.sort(np.vstack([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
_,ec=np.unique(edges,axis=0,return_counts=True)
meta={'vertices':len(verts),'triangles':len(faces),'components':1,'boundary_edges':int((ec==1).sum()),'nonmanifold_edges':int((ec>2).sum()),'voxel_size':STEP}
(out/'sculpt-info.json').write_text(json.dumps(meta,indent=2));print(meta)
