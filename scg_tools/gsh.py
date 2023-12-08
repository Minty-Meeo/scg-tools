# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from __future__ import annotations
from struct import unpack
from typing import BinaryIO, TextIO

from scg_tools.misc import read_exact, tristrip_walk_new

class GCMesh(object):
    class Mesh(object):
        def __init__(self, material_idx: int, primitive_data: list):
            self.material_idx = material_idx
            self.primitive_data = primitive_data
        #
    #

    class Skinning(object):
        def __init__(self, vtx_begin: int, vtx_count: int, joint_idx_a: int, joint_idx_b: int, rank: int, weight_fxdpnt: int):
            self.vtx_begin = vtx_begin
            self.vtx_count = vtx_count
            self.joint_idx_a = joint_idx_a
            self.joint_idx_b = joint_idx_b      # Only used when weight is non-zero or when R trigger debug is turned on (80031354).
            self.rank = rank
            self.weight_fxdpnt = weight_fxdpnt  # fixed-point integer weight, later converted to float.  Zero means simple weight.
        #

        @staticmethod
        def parse(endian, io: BinaryIO) -> GCMesh.Skinning:
            return GCMesh.Skinning(*unpack(f"{endian}HHhhHH", read_exact(io, 12)))
        #
    #

    class CollInfo(object):
        def __init__(self, unused_vec4f: tuple[float], joint_parent: int, radius: float, src_vec4f: tuple[float], dst_vec4f: tuple[float]):
            self.unused_vec4f = unused_vec4f  # Nothing ever reads from or writes to it
            self.joint_parent = joint_parent  # Joint parent
            self.radius = radius              # Collision sphere radius
            self.src_vec4f = src_vec4f        # Collision sphere offset from joint
            self.dst_vec4f = dst_vec4f        # Is overwritten by PSMTXMultVec at 800335ac
        #

        @staticmethod
        def parse(endian, io: BinaryIO) -> GCMesh.CollInfo:
            unused_vec4f = unpack(f"{endian}ffff", io.read(16))       
            [joint_position_idx, radius] = unpack(f"{endian}If", io.read(8))
            src_vec4f = unpack(f"{endian}ffff", io.read(16))
            dst_vec4f = unpack(f"{endian}ffff", io.read(16))
            return GCMesh.CollInfo(unused_vec4f, joint_position_idx, radius, src_vec4f, dst_vec4f)
        #
    #

    def __init__(self, vtx_pos_nrm: list, vtx_uv_coord: list, vtx_color0: list, meshes: list[Mesh], primitive_indirection: list, joints: list, skinnings: list[Skinning], collinfos: list[CollInfo]):
        self.vtx_pos_nrm = vtx_pos_nrm
        self.vtx_uv_coord = vtx_uv_coord
        self.vtx_color0 = vtx_color0
        self.meshes = meshes
        self.primitive_indirection = primitive_indirection
        self.joints = joints
        self.skinnings = skinnings
        self.collinfos = collinfos
    #
    
    @staticmethod
    def parse(endian, io: BinaryIO) -> GCMesh:
        # unk_offs is only notable in heartstn.gsh, which unfortunately is an incredibly broken model, so it's barely helpful for research.
        # unk_offs seems to point to an array of metadata terminated by a word-sized null terminator (0x00000000), except for the files where it doesn't.  Maybe this was phased out by later Santa Cruz Games tooling?
        [joint_count, skinning_count, joint_offs, unk_offs, joint_collinfo_count, joint_collinfo_offs, skinning_offs] = unpack(f"{endian}HHIIIII", read_exact(io, 24))
        [vtx_count, primitive_meta_count, mesh_count, _, vtx_pos_nrm_offs, vtx_uv_coord_offs, vtx_color0_offs] = unpack(f"{endian}IIIIIII", read_exact(io, 28))
        [primitive_meta_offs, primitive_data_offs, primitive_indirection_offs] = unpack(f"{endian}III", read_exact(io, 12))
        [wtf_offs_1, wtf_offs_2, material_idx_offs, mesh_primitive_start_offs, mesh_primitive_size_offs] = unpack(f"{endian}IIIII", read_exact(io, 20))
        assert wtf_offs_1 == wtf_offs_2 == material_idx_offs  # Wtf are these first two for?  They're all the same!

        vtx_pos_nrm_count = (vtx_uv_coord_offs - vtx_pos_nrm_offs) // 24
        assert vtx_pos_nrm_count == vtx_count
        vtx_uv_coord_count = (vtx_color0_offs - vtx_uv_coord_offs) // 8
        if vtx_uv_coord_count != vtx_count: print("vtx_count != texture coordinate count")
        vtx_color0_count = (primitive_meta_offs - vtx_color0_offs) // 4
        if vtx_uv_coord_count != vtx_count: print("vtx_count != vertex color count")

        io.seek(joint_offs)
        joints = [unpack(f"{endian}iiii", read_exact(io, 16)) for _ in range(joint_count)]

        io.seek(joint_collinfo_offs)
        collinfos = [GCMesh.CollInfo.parse(endian, io) for _ in range(joint_collinfo_count)]

        io.seek(skinning_offs)
        skinnings = [GCMesh.Skinning.parse(endian, io) for _ in range(skinning_count)]
        
        io.seek(vtx_pos_nrm_offs)
        vtx_pos_nrm = [unpack(f"{endian}ffffff", read_exact(io, 24)) for _ in range(vtx_pos_nrm_count)]
        
        io.seek(vtx_uv_coord_offs)
        vtx_uv_coord = [unpack(f"{endian}ff", read_exact(io, 8)) for _ in range(vtx_uv_coord_count)]

        io.seek(vtx_color0_offs)
        vtx_color0 = [unpack(f"{endian}BBBB", read_exact(io, 4)) for _ in range(vtx_color0_count)]

        io.seek(primitive_meta_offs)
        primitive_meta = [unpack(f"{endian}HH", read_exact(io, 4)) for _ in range(primitive_meta_count)]

        def read_primitive(idx, size):
            io.seek(primitive_data_offs + idx * 2)
            return unpack(f"{endian}{size}H", read_exact(io, size * 2))
        primitive_data = [read_primitive(idx, size) for [idx, size] in primitive_meta]

        io.seek(primitive_indirection_offs)
        primitive_indirection = [unpack(f"{endian}H", read_exact(io, 2))[0] for _ in range(vtx_uv_coord_count)]

        io.seek(material_idx_offs)
        material_idxs = [unpack(f"{endian}H", read_exact(io, 2))[0] for _ in range(mesh_count)]

        io.seek(mesh_primitive_start_offs)
        mesh_primitive_starts = [unpack(f"{endian}H", read_exact(io, 2))[0] for _ in range(mesh_count)]

        io.seek(mesh_primitive_size_offs)
        mesh_primitive_sizes = [unpack(f"{endian}H", read_exact(io, 2))[0] for _ in range(mesh_count)]

        def make_mesh(i: int):
            head = mesh_primitive_starts[i]; tail = head + mesh_primitive_sizes[i]
            return GCMesh.Mesh(material_idxs[i], primitive_data[head:tail])
        meshes = [make_mesh(i) for i in range(mesh_count)]
            
        return GCMesh(vtx_pos_nrm, vtx_uv_coord, vtx_color0, meshes, primitive_indirection, joints, skinnings, collinfos)
    #

    # weight_fxdpnt notes:
    # 800321d8 > load u16 from joint
    # 800321e8 v
    # 80032208 v
    # 80032234 v
    # 8003223c > integer to float conversion
    # 80032264 > multiply by floating point value 1/65536
    # 8003236c > if greater than 0, run more complex logic

    # 80032cd0 v
    # 80032cd4 v
    # 80032cd8 v
    # 80032cdc > 1 - value is multiplied to three floats.
    # 80032d04 v
    # 80032d0c v
    # 80032d10 > value is multiplied to three floats
    # 80032f64 v
    # 80032f68 v
    # 80032f6c v
    # 80032f70 > 1 - value is multiplied to three floats.
    # 80032fa8 v
    # 80032fac v
    # 80032fb0 > value is multiplied to three floats

    def dump_wavefront_obj(self, io: TextIO, mtl_stemname: str = None) -> None:
        vtx_pos_nrm = [list(x) for x in self.vtx_pos_nrm]
        joint_stack = dict[list[float, float, float, float]]()
        for skinning in self.skinnings:
            if skinning.weight_fxdpnt == 0:
                joint_stack[skinning.rank] = self.joints[skinning.joint_idx_a]
            else:
                # This doesn't work at all.  I don't understand it at all.  Modifying it in memory makes no sense.
                weight = skinning.weight_fxdpnt / 0x10000  # This seems like an off-by-one error, but I think it's more accurate.
                v1 = [f * (1 - weight) for f in self.joints[skinning.joint_idx_a]]
                v2 = [f *      weight  for f in self.joints[skinning.joint_idx_b]]
                joint_stack[skinning.rank] = [f1 + f2 for [f1, f2] in zip(v1, v2)]
            vtx_head = skinning.vtx_begin; vtx_tail = vtx_head + skinning.vtx_count
            for i in range(0, skinning.rank + 1):
                curr_joint: tuple[float, float, float, float] = joint_stack[i]
                for j in range(vtx_head, vtx_tail):
                    vtx_pos_nrm[j][0] += curr_joint[0]
                    vtx_pos_nrm[j][1] += curr_joint[1]
                    vtx_pos_nrm[j][2] += curr_joint[2]
        if mtl_stemname:
            io.write(f"mtllib {mtl_stemname}.mtl\n")
        # TODO: vertex color0
        for [x, y, z, xn, yn, zn] in vtx_pos_nrm:
            io.write(f"v {-x} {-y} {z}\n"
                    f"vn {xn} {yn} {zn}\n")
        for [u, v] in self.vtx_uv_coord:
            io.write(f"vt {u} {-v}\n")
        callback = lambda tri_pos, tri_tex, tri_nrm : io.write("f {}/{}/{} {}/{}/{} {}/{}/{}\n".format(tri_pos[2]+1, tri_tex[2]+1, tri_nrm[2]+1, tri_pos[1]+1, tri_tex[1]+1, tri_nrm[1]+1, tri_pos[0]+1, tri_tex[0]+1, tri_nrm[0]+1))  # Wavefront OBJ is not zero-indexed... eww...
        for mesh in self.meshes:
            io.write("o mesh\n")
            if mtl_stemname:
                io.write(f"usemtl {mtl_stemname}_{mesh.material_idx}\n")
            for primitive in mesh.primitive_data:
                indirect_primitive = [self.primitive_indirection[x] for x in primitive]
                tristrip_walk_new(callback, indirect_primitive, primitive, indirect_primitive)
    #
#
