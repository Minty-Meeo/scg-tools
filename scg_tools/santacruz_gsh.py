from __future__ import annotations
from struct import unpack
from sys import argv
from typing import BinaryIO, TextIO

from scg_tools.misc import read_exact, tristrip_walk_new

class GCMesh(object):
    class Mesh(object):
        def __init__(self, material_idx: int, primitive_data: list):
            self.material_idx = material_idx
            self.primitive_data = primitive_data
        #
    #

    def __init__(self, vtx_pos_nrm: list, vtx_uv_coord: list, vtx_color0: list, meshes: list[GCMesh.Mesh], primitive_indirection: list):
        self.vtx_pos_nrm = vtx_pos_nrm
        self.vtx_uv_coord = vtx_uv_coord
        self.vtx_color0 = vtx_color0
        self.meshes = meshes
        self.primitive_indirection = primitive_indirection
    
    @staticmethod
    def parse(io: BinaryIO) -> GCMesh:
        io.seek(24)
        [vtx_count, primitive_meta_count, mesh_count, _, vtx_pos_nrm_offs, vtx_uv_coord_offs, vtx_color0_offs] = unpack(">IIIIIII", read_exact(io, 28))
        [primitive_meta_offs, primitive_data_offs, primitive_indirection_offs] = unpack(">III", read_exact(io, 12))
        [wtf_offs_1, wtf_offs_2, material_idx_offs, mesh_primitive_start_offs, mesh_primitive_size_offs] = unpack(">IIIII", read_exact(io, 20))
        assert wtf_offs_1 == wtf_offs_2 == material_idx_offs  # Wtf are these first two for?  They're all the same!
        
        vtx_pos_nrm_count = (vtx_uv_coord_offs - vtx_pos_nrm_offs) // 24
        assert vtx_pos_nrm_count == vtx_count
        io.seek(vtx_pos_nrm_offs)
        vtx_pos_nrm = [unpack(">ffffff", read_exact(io, 24)) for _ in range(vtx_pos_nrm_count)]
        
        vtx_uv_coord_count = (vtx_color0_offs - vtx_uv_coord_offs) // 8
        if vtx_uv_coord_count != vtx_count: print("This model is retarded! (tex coord)")
        io.seek(vtx_uv_coord_offs)
        vtx_uv_coord = [unpack(">ff", read_exact(io, 8)) for _ in range(vtx_uv_coord_count)]

        vtx_color0_count = (primitive_meta_offs - vtx_color0_offs) // 4
        if vtx_uv_coord_count != vtx_count: print("This model is retarded! (color0)")
        io.seek(vtx_color0_offs)
        vtx_color0 = [unpack(">BBBB", read_exact(io, 4)) for _ in range(vtx_color0_count)]

        io.seek(primitive_meta_offs)
        primitive_meta = [unpack(">HH", read_exact(io, 4)) for _ in range(primitive_meta_count)]

        def read_primitive(idx, size):
            io.seek(primitive_data_offs + idx * 2)
            return unpack(f">{size}H", read_exact(io, size * 2))
        primitive_data = [read_primitive(idx, size) for [idx, size] in primitive_meta]

        io.seek(primitive_indirection_offs)
        primitive_indirection = [unpack(">H", read_exact(io, 2))[0] for _ in range(vtx_uv_coord_count)]
        # primitives_real = [[primitive_indirection[x] for x in primitive] for primitive in primitive_data]

        io.seek(material_idx_offs)
        material_idxs = [unpack(">H", read_exact(io, 2))[0] for _ in range(mesh_count)]

        io.seek(mesh_primitive_start_offs)
        mesh_primitive_starts = [unpack(">H", read_exact(io, 2))[0] for _ in range(mesh_count)]

        io.seek(mesh_primitive_size_offs)
        mesh_primitive_sizes = [unpack(">H", read_exact(io, 2))[0] for _ in range(mesh_count)]

        meshes = list[GCMesh.Mesh]()
        for i in range(mesh_count):
            begin = mesh_primitive_starts[i]; end = begin + mesh_primitive_sizes[i]
            meshes.append(GCMesh.Mesh(material_idxs[i], primitive_data[begin:end]))
        return GCMesh(vtx_pos_nrm, vtx_uv_coord, vtx_color0, meshes, primitive_indirection)
    #

    def dump_wavefront_obj(self, io: TextIO) -> None:
        # TODO: vertex color0
        for [x, y, z, xn, yn, zn] in self.vtx_pos_nrm:
            io.write(f"v {-x} {-y} {z}\n"
                    f"vn {xn} {yn} {zn}\n")
        for [u, v] in self.vtx_uv_coord:
            io.write(f"vt {u} {v}\n")
        callback = lambda tri_pos, tri_tex, tri_nrm : io.write("f {}/{}/{} {}/{}/{} {}/{}/{}\n".format(tri_pos[2]+1, tri_tex[2]+1, tri_nrm[2]+1, tri_pos[1]+1, tri_tex[1]+1, tri_nrm[1]+1, tri_pos[0]+1, tri_tex[0]+1, tri_nrm[0]+1))  # Wavefront OBJ is not zero-indexed... eww...
        for mesh in self.meshes:
            io.write("o mesh\n")
            for primitive in mesh.primitive_data:
                indirect_primitive = [self.primitive_indirection[x] for x in primitive]
                tristrip_walk_new(callback, indirect_primitive, primitive, indirect_primitive)
    #
#


def main() -> int:
    if len(argv) < 3:
        return 1
    with open(argv[1], "rb") as f:
        gsh = GCMesh.parse(f)
    with open(argv[2], "w") as f:
        gsh.dump_wavefront_obj(f)
#


#
if __name__ == "__main__":
    exit(main())
