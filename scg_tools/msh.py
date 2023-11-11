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

    class FinalData0(object):
        def __init__(self, payload: list, array: list):
            self.payload = payload
            self.array = array
        #

        payload_format = "<xxxx xxxx xxxx xxxx"\
                         " xxxx xxxx xxxx xxxx"\
                         " xxxx xxxx"

        @staticmethod
        def parse(io: BinaryIO) -> PCMesh.FinalData0:
            payload = unpack(PCMesh.FinalData0.payload_format, read_exact(io, 40))
            array = unpack("<HHH2x", read_exact(io, 8))
            return PCMesh.FinalData0(payload, array)
        #
    #

    class FinalData1(object):
        def __init__(self, payload: list,  array: list):
            self.payload = payload
            self.array = array
        #

        payload_format = "<xxxx xxxx xxxx xxxx"\
                         " xxxx xxxx xxxx xxxx"\
                         " xxxx xxxx xxxx xxxx"

        @staticmethod
        def parse(io: BinaryIO) -> PCMesh.FinalData1:
            payload = unpack(PCMesh.FinalData1.payload_format, read_exact(io, 48))
            array = unpack("<HHHH", read_exact(io, 8))
            return PCMesh.FinalData1(payload, array)
        #
    #

    class FinalData4(object):
        def __init__(self, payload_a: list, payload_b: list, array: list):
            self.payload_a = payload_a
            self.payload_b = payload_b
            self.array = array
        #

        payload_format = "<xxxx bbbx xxxx bbxx"\
                         " xxxx bbxx xxxx bbxx"

        @staticmethod
        def parse(io: BinaryIO) -> PCMesh.FinalData4:
            payload_a = unpack(PCMesh.FinalData4.payload_format, read_exact(io, 32))
            payload_b = unpack(PCMesh.FinalData4.payload_format, read_exact(io, 32))
            array = unpack("<HHHH", read_exact(io, 8))
            return PCMesh.FinalData4(payload_a, payload_b, array)
        #
    #

    class FinalData5(object):
        def __init__(self, payload_a: list, payload_b: list, array: list):
            self.payload_a = payload_a
            self.payload_b = payload_b
            self.array = array
        #

        payload_format = "<xxxx bbbx xxxx bbxx"\
                         " xxxx bbxx xxxx bbxx"\
                         " xxxx bbxx"

        @staticmethod
        def parse(io: BinaryIO) -> PCMesh.FinalData5:
            payload_a = unpack(PCMesh.FinalData5.payload_format, read_exact(io, 40))
            payload_b = unpack(PCMesh.FinalData5.payload_format, read_exact(io, 40))
            array = unpack("<HHHHH2x", read_exact(io, 12))
            return PCMesh.FinalData5(payload_a, payload_b, array)
        #
    #

    def __init__(self, vtx_poses: list, joints: list, skinnings: list[PCMesh.Skinning], mysteries: list[bytes], finaldata0s: list[FinalData0], finaldata1s: list[FinalData1], finaldata4s: list[FinalData4], finaldata5s: list[FinalData5]):
        self.vtx_poses = vtx_poses
        self.joints = joints
        self.skinnings = skinnings
        self.mysteries = mysteries
        self.finaldata0s = finaldata0s
        self.finaldata1s = finaldata1s
        self.finaldata4s = finaldata4s
        self.finaldata5s = finaldata5s
    #

    @staticmethod
    def parse(io: BinaryIO) -> PCMesh:
        [vtx_count, finaldata_total_count, joint_count, skinning_count, _, mystery_count] = unpack("<HHHHHH", read_exact(io, 12))
        [joint_offs, vtx_pos_offs, _, _, mystery_offs, _, skinning_offs] = unpack("<IIIIIII", read_exact(io, 28))
        [finaldata0_offs, finaldata1_offs, finaldata2_offs, finaldata3_offs, finaldata4_offs, finaldata5_offs, finaldata6_offs, finaldata7_offs] = unpack("<IIIIIIII", read_exact(io, 32))
        [finaldata0_count, finaldata1_count, finaldata2_count, finaldata3_count, finaldata4_count, finaldata5_count, finaldata6_count, finaldata7_count] = unpack("<HHHHHHHH", read_exact(io, 16))
        # Unused field?
        unused_field = unpack("<I", read_exact(io, 4))[0]
        assert unused_field == 0xCCCCCCCC or unused_field == 0  # Is zero in gourd.msh
        # Additional padding zeroes(?) may follow, e.g. gourd.msh
        # These seem unused.  Let's confirm that.
        assert finaldata2_count == 0 and finaldata2_offs == 0xCCCCCCCC
        assert finaldata3_count == 0 and finaldata3_offs == 0xCCCCCCCC
        # These haven't been observed with non-zero sizes yet.  Sound the alarm if one is seen.
        assert finaldata6_count == 0
        assert finaldata7_count == 0
        # Why does this field exist?  Expand this check if finaldata 2, 3, 6, or 7 are identified.
        expected_finaldata_total_count = finaldata0_count + finaldata1_count + finaldata4_count + finaldata5_count
        if finaldata_total_count != expected_finaldata_total_count:
            print(f"finaldata_total_count doesn't match what's expected, difference of {finaldata_total_count - expected_finaldata_total_count}")
        
        io.seek(vtx_pos_offs)
        vtx_poses = [unpack("<hhhh", read_exact(io, 8)) for _ in range(vtx_count)]

        io.seek(joint_offs)
        joints = [unpack("<iiii", read_exact(io, 16)) for _ in range(joint_count)]

        io.seek(skinning_offs)
        skinnings = [PCMesh.Skinning.parse(io) for _ in range(skinning_count)]

        io.seek(mystery_offs)
        mysteries = [read_exact(io, 12) for _ in range(mystery_count)]
        # idk what this does yet, if anything.
        assert all(mystery == b'\0\0\0\0\0\0\0\0\0\0\0\0' for mystery in mysteries)

        io.seek(finaldata0_offs)
        finaldata0s = [PCMesh.FinalData0.parse(io) for _ in range(finaldata0_count)]

        io.seek(finaldata1_offs)
        finaldata1s = [PCMesh.FinalData1.parse(io) for _ in range(finaldata1_count)]

        io.seek(finaldata4_offs)
        finaldata4s = [PCMesh.FinalData4.parse(io) for _ in range(finaldata4_count)]

        io.seek(finaldata5_offs)
        finaldata5s = [PCMesh.FinalData5.parse(io) for _ in range(finaldata5_count)]

        return PCMesh(vtx_poses, joints, skinnings, mysteries, finaldata0s, finaldata1s, finaldata4s, finaldata5s)
    #

    def dump_wavefront_obj(self, io: TextIO):
        for [x, y, z, w] in self.vtx_poses:
            io.write(f"v {x} {y} {z}\n")
    #
#
