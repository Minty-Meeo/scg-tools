from __future__ import annotations
from struct import unpack
from sys import argv
from typing import BinaryIO, TextIO

from scg_tools.misc import read_exact, tristrip_walk_new, open_helper

class GCMesh(object):
    class Mesh(object):
        def __init__(self, material_idx: int, primitive_data: list):
            self.material_idx = material_idx
            self.primitive_data = primitive_data
        #
    #

    class Joint(object):
        def __init__(self, vtx_begin: int, vtx_count: int, joint_pos_idx: int, debug_a: int, unk3: int, unk4: int):
            self.vtx_begin = vtx_begin
            self.vtx_count = vtx_count
            self.joint_pos_idx = joint_pos_idx  # Just a guess
            self.debug_a = debug_a  # Only read from when R trigger debug is turned on (80031354).
            self.hierarchy = unk3  # Gets converted to a float.  Is this an index, but for what?
            self.unk4 = unk4
        #
    #

    def __init__(self, vtx_pos_nrm: list, vtx_uv_coord: list, vtx_color0: list, meshes: list[GCMesh.Mesh], primitive_indirection: list, joint_positions: list, joints: list[Joint]):
        self.vtx_pos_nrm = vtx_pos_nrm
        self.vtx_uv_coord = vtx_uv_coord
        self.vtx_color0 = vtx_color0
        self.meshes = meshes
        self.primitive_indirection = primitive_indirection
        self.joint_positions = joint_positions
        self.joints = joints
    
    @staticmethod
    def parse(io: BinaryIO) -> GCMesh:
        [joint_positions_count, joint_data_count, joint_positions_offs, mystery_vec4f_data_offs, mystery_vec4f_data_count, unk_offs, joint_data_offs] = unpack(">HHIIIII", read_exact(io, 24))
        [vtx_count, primitive_meta_count, mesh_count, _, vtx_pos_nrm_offs, vtx_uv_coord_offs, vtx_color0_offs] = unpack(">IIIIIII", read_exact(io, 28))
        [primitive_meta_offs, primitive_data_offs, primitive_indirection_offs] = unpack(">III", read_exact(io, 12))
        [wtf_offs_1, wtf_offs_2, material_idx_offs, mesh_primitive_start_offs, mesh_primitive_size_offs] = unpack(">IIIII", read_exact(io, 20))
        assert wtf_offs_1 == wtf_offs_2 == material_idx_offs  # Wtf are these first two for?  They're all the same!

        vtx_pos_nrm_count = (vtx_uv_coord_offs - vtx_pos_nrm_offs) // 24
        assert vtx_pos_nrm_count == vtx_count
        vtx_uv_coord_count = (vtx_color0_offs - vtx_uv_coord_offs) // 8
        if vtx_uv_coord_count != vtx_count: print("This model is retarded! (tex coord)")
        vtx_color0_count = (primitive_meta_offs - vtx_color0_offs) // 4
        if vtx_uv_coord_count != vtx_count: print("This model is retarded! (color0)")

        io.seek(joint_positions_offs)
        joint_positions = [unpack(">iiii", read_exact(io, 16)) for _ in range(joint_positions_count)]

        io.seek(mystery_vec4f_data_offs)
        def read_mystery_vec4f_data():
            unused_vec4f = unpack(">ffff", io.read(16))  # Unused?  Really?  Nothing ever reads from or writes to it.
            joint_position_idx = unpack(">I", io.read(4))[0]  # Is loaded in loop at 80033590 comparing against joint position indices
            unk_float = unpack(">f", io.read(4))[0]  # Is loaded at 80003fbc
            src_vec4f = unpack(">ffff", io.read(16))
            dst_vec4f = unpack(">ffff", io.read(16))  # Starts uninitialized (0xCC bytes), is overwritten by PSMTXMultVec at 800335ac
            return (unused_vec4f, joint_position_idx, unk_float, src_vec4f, dst_vec4f)
        mystery_vec4f_data = [read_mystery_vec4f_data() for _ in range(mystery_vec4f_data_count)]

        io.seek(joint_data_offs)
        joint_data = [unpack(">HHhhHH", read_exact(io, 12)) for _ in range(joint_data_count)]
        
        io.seek(vtx_pos_nrm_offs)
        vtx_pos_nrm = [list(unpack(">ffffff", read_exact(io, 24))) for _ in range(vtx_pos_nrm_count)]
        
        io.seek(vtx_uv_coord_offs)
        vtx_uv_coord = [unpack(">ff", read_exact(io, 8)) for _ in range(vtx_uv_coord_count)]

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

        io.seek(material_idx_offs)
        material_idxs = [unpack(">H", read_exact(io, 2))[0] for _ in range(mesh_count)]

        io.seek(mesh_primitive_start_offs)
        mesh_primitive_starts = [unpack(">H", read_exact(io, 2))[0] for _ in range(mesh_count)]

        io.seek(mesh_primitive_size_offs)
        mesh_primitive_sizes = [unpack(">H", read_exact(io, 2))[0] for _ in range(mesh_count)]

        def make_mesh(i: int):
            head = mesh_primitive_starts[i]; tail = head + mesh_primitive_sizes[i]
            return GCMesh.Mesh(material_idxs[i], primitive_data[head:tail])
        meshes = [make_mesh(i) for i in range(mesh_count)]
        joints = [GCMesh.Joint(*data) for data in joint_data]

        for joint in joints:
            print("{:4} {:4} {:2} {:2} {:2} {:4x}".format(joint.vtx_begin, joint.vtx_count, joint.joint_pos_idx, joint.debug_a, joint.hierarchy, joint.unk4))
            
        return GCMesh(vtx_pos_nrm, vtx_uv_coord, vtx_color0, meshes, primitive_indirection, joint_positions, joints)
    #

    def dump_wavefront_obj(self, io: TextIO) -> None:
        vtx_pos_nrm = self.vtx_pos_nrm
        hierarchy_history = dict()
        for joint in self.joints:
            hierarchy_history[joint.hierarchy] = joint
            vtx_head = joint.vtx_begin; vtx_tail = vtx_head + joint.vtx_count
            for i in range(joint.hierarchy, -1, -1):
                joint_position = self.joint_positions[hierarchy_history[i].joint_pos_idx]
                for j in range(vtx_head, vtx_tail):
                    vtx_pos_nrm[j][0] += joint_position[0]
                    vtx_pos_nrm[j][1] += joint_position[1]
                    vtx_pos_nrm[j][2] += joint_position[2]
        # TODO: vertex color0
        for [x, y, z, xn, yn, zn] in vtx_pos_nrm:
            io.write(f"v {-x} {-y} {z}\n"
                    f"vn {xn} {yn} {zn}\n")
        for [u, v] in self.vtx_uv_coord:
            io.write(f"vt {u} {-v}\n")
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
    print(argv[1])
    with open(argv[1], "rb") as f:
        gsh = GCMesh.parse(f)
    with open_helper(argv[2], "w", True, True) as f:
        gsh.dump_wavefront_obj(f)
#


#
if __name__ == "__main__":
    exit(main())
