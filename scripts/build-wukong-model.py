"""Convert the original Wukong implicit sculpt into the Jelly Baby cage format."""
import json, math, runpy, struct
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from skimage.measure import marching_cubes

ROOT = Path(__file__).resolve().parents[1]
state = runpy.run_path(str(ROOT / "scripts/wukong-sculpt-source.py"))
field = state["F"]
field_origin = np.asarray(state["origin"], dtype=np.float64)
field_step = float(state["STEP"])


def read_surface(path):
    data = path.read_bytes()
    nv, ni = struct.unpack_from("<II", data)
    vertices = np.frombuffer(data, "<f4", nv * 3, 8).reshape(-1, 3).astype(np.float64)
    faces = np.frombuffer(data, "<u4", ni, 8 + nv * 12).reshape(-1, 3).copy()
    return vertices, faces


def largest_component(vertices, faces):
    edges = np.vstack((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
    graph = coo_matrix((np.ones(len(edges)), (edges[:, 0], edges[:, 1])), shape=(len(vertices), len(vertices)))
    count, labels = connected_components(graph, directed=False)
    if count == 1:
        return vertices, faces
    keep = labels == np.argmax(np.bincount(labels))
    ids = np.full(len(vertices), -1, dtype=np.int64)
    ids[keep] = np.arange(keep.sum())
    good = np.all(keep[faces], axis=1)
    return vertices[keep], ids[faces[good]].astype(np.uint32)


def vertex_normals(vertices, faces):
    tri = vertices[faces]
    normals = np.zeros_like(vertices)
    fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    for corner in range(3):
        np.add.at(normals, faces[:, corner], fn)
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
    return normals


raw_vertices, faces = read_surface(ROOT / "dist/wukong-sculpt.bin")
height = np.ptp(raw_vertices[:, 1])
scale = 0.07 / height
center = (raw_vertices.min(axis=0) + raw_vertices.max(axis=0)) * 0.5
vertices = raw_vertices.copy()
vertices[:, 0] -= center[0]
vertices[:, 2] -= center[2]
vertices[:, 1] -= raw_vertices[:, 1].min()
vertices *= scale
normals = vertex_normals(vertices, faces)


def signed_sample(world):
    raw = np.empty_like(world)
    raw[:, 0] = world[:, 0] / scale + center[0]
    raw[:, 1] = world[:, 1] / scale + raw_vertices[:, 1].min()
    raw[:, 2] = world[:, 2] / scale + center[2]
    coords = ((raw - field_origin) / field_step).T
    return map_coordinates(field, coords, order=1, mode="constant", cval=8.0)


H = 0.0075
lo = vertices.min(axis=0)
hi = vertices.max(axis=0)
origin = np.floor(lo / H) * H - H * 0.25
dims = np.ceil((hi - origin) / H).astype(int) + 1
corners = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]], dtype=int)
splits = np.array([[0, 5, 1, 6], [0, 1, 2, 6], [0, 2, 3, 6], [0, 3, 7, 6], [0, 7, 4, 6], [0, 4, 5, 6]], dtype=int)
cells = set()
for z in range(dims[2]):
    for y in range(dims[1]):
        for x in range(dims[0]):
            points = origin + (corners + [x, y, z]) * H
            if np.any(signed_sample(points) < 0):
                cells.add((x, y, z))
vertex_cells = np.floor((vertices - origin) / H).astype(int)
cells.update(map(tuple, vertex_cells))

particles = []
node_ids = {}


def node(x, y, z):
    key = (x, y, z)
    if key not in node_ids:
        node_ids[key] = len(particles)
        particles.append(origin + np.array(key) * H)
    return node_ids[key]


tets = []
volumes = []
cell_tets = {}
for cell in sorted(cells):
    ids = np.array([node(*(np.array(cell) + c)) for c in corners], dtype=np.uint32)
    cell_tets[cell] = []
    for split in splits:
        tet = ids[split].copy()
        p = np.asarray([particles[i] for i in tet])
        dm = np.column_stack((p[1] - p[0], p[2] - p[0], p[3] - p[0]))
        if np.linalg.det(dm) < 0:
            tet[[1, 2]] = tet[[2, 1]]
            p = np.asarray([particles[i] for i in tet])
            dm = np.column_stack((p[1] - p[0], p[2] - p[0], p[3] - p[0]))
        samples = []
        for a in range(4):
            for amount in (0.25, 0.55, 0.85):
                weights = np.full(4, (1 - amount) / 3)
                weights[a] = amount
                samples.append(weights @ p)
        occupied = np.count_nonzero(signed_sample(np.asarray(samples)) < 0)
        cell_tets[cell].append(len(tets))
        tets.append(tet)
        volumes.append(np.linalg.det(dm) / 6 * max(0.08, occupied / 12))
particles = np.asarray(particles, dtype=np.float64)
tets = np.asarray(tets, dtype=np.uint32)
volumes = np.asarray(volumes, dtype=np.float64)

tri = vertices[faces]
mesh_volume = abs(np.einsum("ij,ij->i", tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6)
volumes *= mesh_volume / volumes.sum()


def embed(points):
    binding_ids = np.empty((len(points), 4), dtype=np.uint32)
    binding_weights = np.empty((len(points), 4), dtype=np.float64)
    tet_ids = np.empty(len(points), dtype=np.uint32)
    point_cells = np.floor((points - origin) / H).astype(int)
    for i, (point, cell) in enumerate(zip(points, point_cells)):
        key = tuple(cell)
        candidates = cell_tets.get(key, [])
        best = None
        for tid in candidates:
            ids = tets[tid]
            p = particles[ids]
            bary123 = np.linalg.solve(np.column_stack((p[1] - p[0], p[2] - p[0], p[3] - p[0])), point - p[0])
            weights = np.r_[1 - bary123.sum(), bary123]
            score = weights.min()
            if best is None or score > best[0]:
                best = (score, tid, ids, weights)
            if score >= -1e-7:
                break
        if best is None:
            raise RuntimeError(f"No cage cell for vertex {i}")
        _, tid, ids, weights = best
        binding_ids[i] = ids
        binding_weights[i] = weights
        tet_ids[i] = tid
    return binding_ids, binding_weights, tet_ids


binding_ids, binding_weights, tet_ids = embed(vertices)
contacts = set()
for cell in cells:
    ids = np.flatnonzero(np.all(vertex_cells == cell, axis=1))
    if not len(ids):
        continue
    for axis in range(3):
        contacts.add(int(ids[np.argmin(vertices[ids, axis])]))
        contacts.add(int(ids[np.argmax(vertices[ids, axis])]))

# A lower-resolution closed optical surface from the same implicit volume.
factor = 3
opt_v, opt_f, _, _ = marching_cubes(field[::factor, ::factor, ::factor], 0, spacing=(field_step * factor,) * 3, allow_degenerate=False)
opt_v += field_origin
opt_v, opt_f = largest_component(opt_v, opt_f.astype(np.uint32))
opt_v[:, 0] -= center[0]
opt_v[:, 2] -= center[2]
opt_v[:, 1] -= raw_vertices[:, 1].min()
opt_v *= scale
opt_tri = opt_v[opt_f]
if np.einsum("ij,ij->i", opt_tri[:, 0], np.cross(opt_tri[:, 1], opt_tri[:, 2])).sum() < 0:
    opt_f = opt_f[:, [0, 2, 1]]
opt_n = vertex_normals(opt_v, opt_f)
opt_binding_ids, opt_binding_weights, _ = embed(opt_v)

# Three-neighbour interpolation transfers optical thickness to the visible skin.
dist, nearest = cKDTree(opt_v).query(vertices, k=3)
weights = 1 / np.maximum(dist, 1e-8)
weights /= weights.sum(axis=1, keepdims=True)

arrays = {
    "positions": vertices.astype("<f4").ravel(),
    "normals": normals.astype("<f4").ravel(),
    "indices": faces.astype("<u4").ravel(),
    "particles": particles.astype("<f8").ravel(),
    "tets": tets.astype("<u4").ravel(),
    "volumes": volumes.astype("<f8"),
    "bindingIds": binding_ids.astype("<u4").ravel(),
    "bindingWeights": binding_weights.astype("<f8").ravel(),
    "tetIds": tet_ids.astype("<u4"),
    "contacts": np.asarray(sorted(contacts), dtype="<u4"),
    "opticalPositions": opt_v.astype("<f4").ravel(),
    "opticalNormals": opt_n.astype("<f4").ravel(),
    "opticalIndices": opt_f.astype("<u4").ravel(),
    "opticalBindingIds": opt_binding_ids.astype("<u4").ravel(),
    "opticalBindingWeights": opt_binding_weights.astype("<f8").ravel(),
    "thicknessIds": nearest.astype("<u4").ravel(),
    "thicknessWeights": weights.astype("<f4").ravel(),
}
chunks = []
layout = {}
offset = 0
for name, array in arrays.items():
    padding = (8 - offset % 8) % 8
    if padding:
        chunks.append(bytes(padding))
        offset += padding
    layout[name] = {"offset": offset, "length": int(array.size), "type": array.dtype.name}
    blob = array.tobytes()
    chunks.append(blob)
    offset += len(blob)
(ROOT / "src/assets/model/wukong.bin").write_bytes(b"".join(chunks))
(ROOT / "src/assets/model/wukong.json").write_text(json.dumps({"sourceHash": "reference-chibi-wukong-v3", "scale": scale, "bottom": float(raw_vertices[:, 1].min()), "volume": mesh_volume, "layout": layout}, indent=2))
print({"visibleVertices": len(vertices), "visibleTriangles": len(faces), "particles": len(particles), "tets": len(tets), "opticalVertices": len(opt_v), "opticalTriangles": len(opt_f), "contacts": len(contacts), "volume": mesh_volume})
