"""Blender-independent 3D actor math: planar two-bone IK and normalized, pose-evaluated mesh skinning.

These functions control **actual 3D mesh vertices**. They intentionally do not certify
Blender armature modifiers, anatomical correctness, cinematography or subjective acting.
"""
from __future__ import annotations
import math
import numpy as np


def smooth(a: float, b: float, t: float) -> float:
    if b <= a: return 1.0 if t >= b else 0.0
    u = max(0., min(1., (t-a)/(b-a)))
    return u*u*(3.0-2.0*u)


def tween(t: float, keys: list[list[float]]) -> float:
    if not keys: raise ValueError('Empty motion curve')
    if t <= keys[0][0]: return keys[0][1]
    for (a, va), (b, vb) in zip(keys, keys[1:]):
        if t <= b:
            return va + (vb-va)*smooth(a,b,t)
    return keys[-1][1]


def solve_ik_xz(shoulder, target, upper: float, lower: float, bend: int = -1):
    """Return a 3D elbow and wrist for a two-link limb constrained in the x-z plane.

    Targets beyond reach are rejected, NEVER teleported or silently clamped.
    """
    a=np.asarray(shoulder,dtype=float); p=np.asarray(target,dtype=float)
    if a.shape != (3,) or p.shape != (3,) or not np.isfinite(a).all() or not np.isfinite(p).all():
        raise ValueError('Invalid IK points')
    if upper <= 0 or lower <= 0 or not all(math.isfinite(v) for v in (upper,lower)):
        raise ValueError('Invalid bone lengths')
    dx, dz = p[0]-a[0], p[2]-a[2]
    d=math.hypot(dx,dz)
    if d > upper+lower+1e-6 or d < abs(upper-lower)-1e-6 or d < 1e-8:
        raise ValueError(f'IK target unreachable (distance={d:.4f})')
    d=max(1e-8,d)
    direction=math.atan2(dz,dx)
    c=max(-1.,min(1.,(upper*upper+d*d-lower*lower)/(2*upper*d)))
    alpha=math.acos(c)
    theta=direction+ (1 if bend>0 else -1)*alpha
    elbow=np.array([a[0]+upper*math.cos(theta),a[1],a[2]+upper*math.sin(theta)])
    wrist=p.copy()
    if abs(upper-np.linalg.norm((elbow-a)[[0,2]]))>1e-5 or abs(lower-np.linalg.norm((p-elbow)[[0,2]]))>1e-5:
        raise ValueError('IK geometric invariant failed')
    return elbow,wrist


def segment_rigid_map(vertices:np.ndarray,old_a,old_b,new_a,new_b):
    """Rigid XY-plane rotation around Y mapping rest bone A->B onto pose bone A->B.

    Rest and pose segment lengths must match; coordinates use X/Y/Z; segments in XZ.
    """
    old_a=np.asarray(old_a,float);old_b=np.asarray(old_b,float)
    new_a=np.asarray(new_a,float);new_b=np.asarray(new_b,float)
    v=np.asarray(vertices,float)
    d0=old_b-old_a;d1=new_b-new_a
    l0=np.linalg.norm(d0[[0,2]]); l1=np.linalg.norm(d1[[0,2]])
    if l0<1e-8 or l1<1e-8 or abs(l0-l1)>1e-3:raise ValueError('Bone length drift')
    theta=math.atan2(d1[2],d1[0])-math.atan2(d0[2],d0[0])
    # In X-Z coordinates this is a counterclockwise 2D rotation.
    c,s=math.cos(theta),math.sin(theta)
    shifted=v-old_a
    out=np.empty_like(v)
    out[:,0]=new_a[0]+shifted[:,0]*c-shifted[:,2]*s
    out[:,1]=new_a[1]+shifted[:,1]
    out[:,2]=new_a[2]+shifted[:,0]*s+shifted[:,2]*c
    return out


def weighted_lbs(vertices,weights,mappings):
    """Apply evaluated 3D linear blend skinning using explicit normalized vertex weights.

    mappings lists (rest_A,rest_B,pose_A,pose_B); vertex groups assigned by columns.
    """
    rest=np.asarray(vertices,float); w=np.asarray(weights,float)
    if rest.ndim!=2 or rest.shape[1]!=3 or w.shape!=(len(rest),len(mappings)):
        raise ValueError('Invalid vertex/weight dimensions')
    if not (np.isfinite(rest).all() and np.isfinite(w).all()):raise ValueError('Nonfinite vertices/weights')
    if (w < -1e-8).any() or not np.allclose(w.sum(axis=1),1.,atol=1e-5):
        raise ValueError('Each vertex must have normalized nonnegative skin weights')
    moved=np.zeros_like(rest)
    for i,m in enumerate(mappings):
        moved+=segment_rigid_map(rest,*m)*w[:,i,None]
    return moved


def skinned_tube(shoulder,elbow,wrist, *, sections=29, sides=16, radius=.15):
    """Organic-looking continuous two-bone mesh with smooth elbow blending, no split parts."""
    a=np.asarray(shoulder,float); b=np.asarray(elbow,float); c=np.asarray(wrist,float)
    if sections<12 or sides<8:raise ValueError('Mesh density too low')
    # Rest bone vectors must be collinear and nearly vertical for this initial authored tube.
    if not (abs(a[0]-b[0])<1e-6 and abs(a[0]-c[0])<1e-6):
        raise ValueError('Tube rest pose must be straight')
    verts=[]; weights=[]; faces=[]
    for j in range(sections):
        q=j/(sections-1)
        if q<=.5: center=a+(b-a)*(q*2)
        else: center=b+(c-b)*((q-.5)*2)
        taper=.76+.21*math.sin(math.pi*q)
        if q>.88:taper*=1-.28*smooth(.88,1.,q)
        if q<.05:taper*=.9+.1*smooth(0,.05,q)
        for k in range(sides):
            ang=2*math.pi*k/sides
            verts.append([center[0]+radius*taper*math.cos(ang),center[1]+radius*.86*taper*math.sin(ang),center[2]])
            # Smooth influence through the anatomical elbow, sampled over real geometry.
            upper=1.-smooth(.37,.63,q)
            weights.append([upper,1.-upper])
    for j in range(sections-1):
        for k in range(sides):
            aa=j*sides+k; bb=j*sides+(k+1)%sides
            cc=(j+1)*sides+k; dd=(j+1)*sides+(k+1)%sides
            faces.append((aa,cc,dd));faces.append((aa,dd,bb))
    faces.append(tuple(range(sides-1,-1,-1)))
    faces.append(tuple((sections-1)*sides+k for k in range(sides)))
    return np.asarray(verts,float),np.asarray(weights,float),faces


def deformation_measure(rest,moved)->float:
    a=np.asarray(rest);b=np.asarray(moved)
    if a.shape!=b.shape:return 0.0
    return float(np.max(np.linalg.norm(b-a,axis=1)))
