# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from __future__ import annotations
from typing import BinaryIO, TextIO
from struct import unpack

from scg_tools.misc import read_exact
from scg_tools.misc import tristrip_walk

class PCMesh(object):
    class Skinning(object):
        def __init__(self, vtx_begin: int, vtx_count: int, joint_idx_a: int, joint_idx_b: int, rank: int, weight_fxdpnt: int):
            self.vtx_begin = vtx_begin
            self.vtx_count = vtx_count
            self.joint_idx_a = joint_idx_a
            self.joint_idx_b = joint_idx_b
            self.rank = rank
            self.weight_fxdpnt = weight_fxdpnt  # fixed-point integer weight, later converted to float.  Zero means simple weight.
        #

        @staticmethod
        def parse(io: BinaryIO) -> PCMesh.Skinning:
            return PCMesh.Skinning(*unpack("<HHhhHH", read_exact(io, 12)))
        #
    #

    class SemiFinalData(object):
        def __init__(self, data_a: list, data_b: list, array: list):
            self.data_a = data_a
            self.data_b = data_b
            self.array = array
        #

        data_format = "<xxxx bbbx xxxx bbxx"\
                      " xxxx bbxx xxxx bbxx"

        @staticmethod
        def parse(io: BinaryIO) -> PCMesh.SemiFinalData:
            data_a = unpack(PCMesh.SemiFinalData.data_format, read_exact(io, 32))
            data_b = unpack(PCMesh.SemiFinalData.data_format, read_exact(io, 32))
            array = unpack("<HHHH", read_exact(io, 8))
            return PCMesh.SemiFinalData(data_a, data_b, array)
        #
    #

    class FinalData(object):
        def __init__(self, data_a: list, data_b: list, array: list):
            self.data_a = data_a
            self.data_b = data_b
            self.array = array
        #

        data_format = "<xxxx bbbx xxxx bbxx"\
                      " xxxx bbxx xxxx bbxx"\
                      " xxxx bbxx"

        @staticmethod
        def parse(io: BinaryIO) -> PCMesh.FinalData:
            data_a = unpack(PCMesh.FinalData.data_format, read_exact(io, 40))
            data_b = unpack(PCMesh.FinalData.data_format, read_exact(io, 40))
            array = unpack("<HHHHH2x", read_exact(io, 12))
            return PCMesh.FinalData(data_a, data_b, array)
        #
    #

    def __init__(self, vtx_poses: list, joints: list, skinnings: list[PCMesh.Skinning], semifinaldatas: list[SemiFinalData], finaldatas: list[FinalData]):
        self.vtx_poses = vtx_poses
        self.joints = joints
        self.skinnings = skinnings
        self.semifinaldatas = semifinaldatas
        self.finaldatas = finaldatas
    #

    @staticmethod
    def parse(io: BinaryIO) -> PCMesh:
        [vtx_count, unk_count, joint_count, skinning_count, _, mystery_count] = unpack("<HHHHHH", read_exact(io, 12))
        [joint_offs, vtx_pos_offs, _, _, mystery_offs, _, skinning_offs] = unpack("<IIIIIII", read_exact(io, 28))
        [semifinaldata_offs, semifinaldata_offs2, _, _, semifinaldata_offs3, finaldata_offs, _, _, _, _, semifinaldata_count, finaldata_count, _, _] = unpack("<IIIIIIIIIIHHII", read_exact(io, 52))
        # Sanity testing (hopefully will be removed)
        assert semifinaldata_offs == semifinaldata_offs2 == semifinaldata_offs3
        
        io.seek(vtx_pos_offs)
        vtx_poses = [unpack("<hhhh", read_exact(io, 8)) for _ in range(vtx_count)]

        io.seek(joint_offs)
        joints = [unpack("<iiii", read_exact(io, 16)) for _ in range(joint_count)]

        io.seek(skinning_offs)
        skinnings = [PCMesh.Skinning.parse(io) for _ in range(skinning_count)]

        io.seek(semifinaldata_offs)
        semifinaldatas = [PCMesh.SemiFinalData.parse(io) for _ in range(semifinaldata_count)]

        io.seek(finaldata_offs)
        finaldatas = [PCMesh.FinalData.parse(io) for _ in range(finaldata_count)]

        return PCMesh(vtx_poses, joints, skinnings, semifinaldatas, finaldatas)
    #

    def dump_wavefront_obj(self, io: TextIO):
        for [x, y, z, w] in self.vtx_poses:
            io.write(f"v {x} {y} {z}\n")
        io.write("o mesh\n")
        for finaldata in self.finaldatas:
            pass
    #
#
