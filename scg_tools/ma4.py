# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from __future__ import annotations
from binascii import hexlify, unhexlify
from io import BytesIO
from struct import unpack, pack
from typing import BinaryIO, TextIO

from scg_tools.misc import read_exact, read_c_string, align_up, tristrip_walk
from scg_tools.tex import parse_psxtexfile, write_psxtexfile

codepage = "windows-1250"

class Prop(object):
    class Mesh(object):
        def __init__(self, material_idx: int, primitive_data: list):
            self.material_idx = material_idx
            self.primitive_data = primitive_data
        #

        def __eq__(self, other: Prop.Mesh):
            return self.material_idx == other.material_idx and self.primitive_data == other.primitive_data
        #
    #

    old_format_parse = False
    old_format_write = False

    def __init__(self, vertexes: list, meshes: list[Prop.Mesh], name: bytes):
        self.vertexes = vertexes
        self.meshes = meshes
        self.name = name
    #

    @staticmethod
    def parse(endian, io: BinaryIO, prop_data_base: int, prop_name_base: int) -> Prop:
        io.seek(prop_data_base)
        [vtx_count, primitive_meta_count, mesh_count, vtx_base, unused, primitive_meta_base, primitive_data_base, material_idx_base, mesh_primitives_start_base, mesh_primitives_size_base] = unpack(f"{endian}IIIIIIIIII", read_exact(io, 40))
        assert unused == 0, "Prop metadata thought to be unused was found with a value other than zero!  What does that mean?"
        io.seek(prop_name_base)
        name = read_c_string(io)

        # UV coords, XYZ pos, XYZ normal(?), RGBA
        vertexes = list()
        io.seek(prop_data_base + vtx_base)
        if Prop.old_format_parse:
            for _ in range(vtx_count):
                vertexes.append(unpack(f"{endian}ffffffffBBBB", read_exact(io, 36)))
        else:
            for _ in range(vtx_count):
                vertexes.append(unpack(f"{endian}hhhhhhhhBBBB", read_exact(io, 20)))
        
        primitive_meta = list()
        io.seek(prop_data_base + primitive_meta_base)
        for _ in range(primitive_meta_count):
            primitive_meta.append(unpack(f"{endian}HH", read_exact(io, 4)))
        
        primitive_data = list()
        for [idx, size] in primitive_meta:
            io.seek(prop_data_base + primitive_data_base + idx * 2)
            primitive_data.append(unpack(f"{endian}{size}H", read_exact(io, size * 2)))
        
        io.seek(prop_data_base + material_idx_base)
        material_idxs = unpack(f"{endian}{mesh_count}H", read_exact(io, mesh_count * 2))
        io.seek(prop_data_base + mesh_primitives_start_base)
        mesh_primitive_starts = unpack(f"{endian}{mesh_count}H", read_exact(io, mesh_count * 2))
        io.seek(prop_data_base + mesh_primitives_size_base)
        mesh_primitive_sizes = unpack(f"{endian}{mesh_count}H", read_exact(io, mesh_count * 2))

        meshes = list[Prop.Mesh]()
        for i in range(mesh_count):
            begin = mesh_primitive_starts[i]; end = begin + mesh_primitive_sizes[i]
            meshes.append(Prop.Mesh(material_idxs[i], primitive_data[begin:end]))

        return Prop(vertexes, meshes, name)
    #

    def write_data(self, endian, io: BinaryIO) -> int:
        filepos_base = io.tell()
        io.seek(filepos_base + 40)

        vtx_base = io.tell() - filepos_base
        # 8003dc58 GXSetVtxAttrFmt(GX_VTXFMT6, GX_VA_POS , GX_POS_XYZ , GX_S16  ,  0)
        # 8003dc70 GXSetVtxAttrFmt(GX_VTXFMT6, GX_VA_CLR0, GX_CLR_RGBA, GX_RGBA8,  0)
        # 8003dc88 GXSetVtxAttrFmt(GX_VTXFMT6, GX_VA_TEX0, GX_TEX_ST  , GX_S16  , 12) <= Fixed-point decimal, divide by 2^12
        # 8003dca0 GXSetVtxAttrFmt(GX_VTXFMT6, GX_VA_NRM,  GX_NRM_XYZ , GX_S16  ,  0) <= Is this an oversight?
        if Prop.old_format_write:
            if Prop.old_format_parse:
                for vtx in self.vertexes:
                    io.write(pack(f"{endian}ffffffffBBBB", *vtx))
            else:
                for vtx in self.vertexes:
                    [u, v, x, y, z, xn, yn, zn, r, g, b, a] = vtx
                    u = u / 4096; v = v / 4096; x = float(x); y = float(y); z = float(z); xn = float(xn); yn = float(yn); zn = float(zn)
                    io.write(pack(f"{endian}ffffffffBBBB", u, v, x, y, z, xn, yn, zn, r, g, b, a))
        else:
            if Prop.old_format_parse:
                for vtx in self.vertexes:
                    [u, v, x, y, z, xn, yn, zn, r, g, b, a] = vtx
                    u = round(u * 4096); v = round(v * 4096); x = round(x); y = round(y); z = round(z); xn = round(xn); yn = round(yn); zn = round(zn)
                    io.write(pack(f"{endian}hhhhhhhhBBBB", u, v, x, y, z, xn, yn, zn, r, g, b, a))
            else:
                for vtx in self.vertexes:
                    io.write(pack(f"{endian}hhhhhhhhBBBB", *vtx))

        # Write Primitive Meta (idx and size)
        primitive_meta_base = io.tell() - filepos_base
        primitive_meta_count = 0
        primitive_meta_last = 0
        for mesh in self.meshes:
            for primitive in mesh.primitive_data:
                io.write(pack(f"{endian}HH", primitive_meta_last, len(primitive)))
                primitive_meta_last += len(primitive)
                primitive_meta_count += 1
        
        # Write Primitive Data
        primitive_data_base = io.tell() - filepos_base
        for mesh in self.meshes:
            for primitive in mesh.primitive_data:
                size = len(primitive)
                io.write(pack(f"{endian}{size}H", *primitive))
        
        # Write Mesh Material Index
        material_idx_base = io.tell() - filepos_base
        for mesh in self.meshes:
            io.write(pack(f"{endian}H", mesh.material_idx))

        # Write Mesh Primitive Starts
        mesh_primitives_start_base = io.tell() - filepos_base
        mesh_primitive_start_last = 0
        for mesh in self.meshes:
            io.write(pack(f"{endian}H", mesh_primitive_start_last))
            mesh_primitive_start_last += len(mesh.primitive_data)

        # Write Mesh Primitive Sizes
        mesh_primitives_size_base = io.tell() - filepos_base
        for mesh in self.meshes:
            io.write(pack(f"{endian}H", len(mesh.primitive_data)))
                
        vtx_count = len(self.vertexes)
        mesh_count = len(self.meshes)

        filepos_back = io.tell()
        io.seek(filepos_base)
        io.write(pack(f"{endian}IIIIIIIIII", vtx_count, primitive_meta_count, mesh_count, vtx_base, 0, primitive_meta_base, primitive_data_base, material_idx_base, mesh_primitives_start_base, mesh_primitives_size_base))
        io.seek(filepos_back)

        return filepos_base
    #

    def write_name(self, io: BinaryIO) -> int:
        filepos_base = io.tell()
        io.write(self.name + b'\0')
        return filepos_base
    #

    def __eq__(self, other: Prop):
        return self.vertexes == other.vertexes and self.meshes == other.meshes and self.name == other.name
    #

    def dump_wavefront_obj(self, io: TextIO) -> None:
        if Prop.old_format_parse:
            for [u, v, x, y, z, xn, yn, zn, r, g, b, a] in self.vertexes:
                x = -x; y = -y; r = r / 255; g = g / 255; b = b / 255
                io.write(f"v {x} {y} {z} {r} {g} {b}\n"  # Sorry, no alpha
                            f"vn {xn} {yn} {zn}\n"
                            f"vt {u} {v}\n")
        else:
            for [u, v, x, y, z, xn, yn, zn, r, g, b, a] in self.vertexes:
                u = u / 4096; v = -v / 4096; x = -x; y = -y; r = r / 255; g = g / 255; b = b / 255
                io.write(f"v {x} {y} {z} {r} {g} {b}\n"  # Sorry, no alpha
                         f"vn {xn} {yn} {zn}\n"
                         f"vt {u} {v}\n")
        callback = lambda tri : io.write("f {0:}/{0:}/{0:} {1:}/{1:}/{1:} {2:}/{2:}/{2:}\n".format(tri[2]+1, tri[1]+1, tri[0]+1))  # Wavefront OBJ is not zero-indexed... eww...
        for mesh in self.meshes:
            io.write("o {:s}\n".format(self.name.decode(codepage)))
            for primitive in mesh.primitive_data:
                tristrip_walk(callback, primitive)
    #
#

class PropList(list[Prop]):
    @staticmethod
    def parse(endian, io: BinaryIO) -> PropList:
        prop_list = PropList()
        prop_list.unkflt, count = unpack(f"{endian}fI", read_exact(io, 8))
        print("unkflt: {}   prop count: {:d}".format(prop_list.unkflt, count))
        prop_data_bases = unpack(f"{endian}{count}I", read_exact(io, count * 4))
        prop_name_bases = unpack(f"{endian}{count}I", read_exact(io, count * 4))
        for n in range(count):
            prop_list.append(Prop.parse(endian, io, prop_data_bases[n], prop_name_bases[n]))
        return prop_list
    #

    def __eq__(self, other: PropList):
        return self.unkflt == other.unkflt and super().__eq__(other)
    #

    def write(self, endian, io: BinaryIO):
        filepos_base = io.tell(); count = len(self)
        io.seek(filepos_base + 8 + count * 4 * 2)
        prop_data_bases = list[int](); prop_name_bases = list[int]()
        # Technically not necessary to do this in two passes, but that's how the original files are laid out.
        for prop in self:
            prop_data_bases.append(prop.write_data(endian, io) - filepos_base)
        for prop in self:
            prop_name_bases.append(prop.write_name(io) - filepos_base)
        filepos_back = io.tell()
        io.seek(filepos_base)
        io.write(pack(f"{endian}fI", self.unkflt, count))
        io.write(pack(f"{endian}{count}I", *prop_data_bases))
        io.write(pack(f"{endian}{count}I", *prop_name_bases))
        io.seek(filepos_back)
    #
#

class Packet(object):
    def __init__(self, type: int, unk: int, data: int, stupid: bool):
        self.type = type
        self.unk = unk
        self.data = data
        self.stupid = stupid  # size == 0 instead of 3
    #

    def __eq__(self, other: Packet):
        return self.type == other.type and self.unk == other.unk and self.data == other.data and self.stupid == other.stupid
    #

    def json_dump(self):
        return {"type": self.type, "unk": self.unk, "data": hexlify(self.data, " ", 4).decode(), "stupid": self.stupid}
    #

    @staticmethod
    def json_load(vals: dict) -> Packet:
        return Packet(vals["type"], vals["unk"], unhexlify(vals["data"].replace(" ", "")), vals["stupid"])
    #
#

class PacketList(list[Packet]):
    @staticmethod
    def parse(io: BinaryIO) -> PacketList:
        packet_list = PacketList()
        while True:
            meta = read_exact(io, 4)
            if unpack("<i", meta)[0] == -1:
                break
            [type, unk, size] = unpack("<HBB", meta)
            stupid = False
            if size == 0: size = 3; stupid = True  # See 800243f8
            data = read_exact(io, size * 4)
            packet_list.append(Packet(type, unk, data, stupid))
        return packet_list
    #

    def write(self, io: BinaryIO):
        for packet in self:
            if packet.stupid:
                assert len(packet.data) // 4 == 3, "Stupid packet is not 12 bytes large (size != 3)."
                io.write(pack("<HBB", packet.type, packet.unk, 0))
            else:
                io.write(pack("<HBB", packet.type, packet.unk, len(packet.data) // 4))
            io.write(packet.data)
        io.write(pack("<i", -1))
    #
            
    def at(self, type: int) -> bytes:
        for packet in self:
            if packet.type == type:
                return packet.data
        raise IndexError("Packet of type {:d} not found".format(type))
    #

    def json_dump(self):
        return [packet.json_dump() for packet in self]
    #

    @staticmethod
    def json_load(vals: list) -> PacketList:
        return PacketList([Packet.json_load(packet_vals) for packet_vals in vals])
    #
#

class CHKFMAPError(Exception):
    pass
#

class Chunk(object):
    def __init__(self, chkfmap: CHKFMAP):
        self.chkfmap = chkfmap
    #

    def parse(self, io: BinaryIO):
        self.raw = io.read()
    #

    def write(self, io: BinaryIO):
        io.write(self.raw)
    #
#

def make_subreader(io: BinaryIO, size: int):
    return BytesIO(read_exact(io, size))
#

class Header(Chunk):
    class SubHeader(object):
        def __init__(self, tid: bytes, cid: bytes, ver: bytes, offs: int, size: int):
            self.tid = tid
            self.cid = cid
            self.ver = ver
            self.offs = offs
            self.size = size
            self.chunk: Chunk
        #
    #

    def __init__(self, chkfmap: CHKFMAP):
        super().__init__(chkfmap)
        self.subheaders = list[Header.SubHeader]()
    #

    def parse(self, io: BinaryIO):
        filepos_base = io.tell()
        nchunks = unpack("<I", read_exact(io, 4))[0]
        print("//////////////////////////////////////////////////////")
        print("LoadSubHeader()")
        print("loading sub header at offset {:08x}".format(filepos_base))
        print("header nchunks {:d}".format(nchunks))
        for n in range(nchunks):
            [tid, cid, ver, offs, size] = unpack("<4s4s4sII", read_exact(io, 20))
            self.subheaders.append(Header.SubHeader(tid, cid, ver, offs, size))
            print("chunk {:04x} offs {:08x} size {:08x} TID < {} > CID < {} > VER < {} > filepos {:08x}".format(n, offs, size, tid.decode(), cid.decode(), ver.decode(), filepos_base + offs))
        print("//////////////////////////////////////////////////////")
        for [n, subheader] in enumerate(self.subheaders):
            io.seek(filepos_base + subheader.offs)
            match subheader.tid:
                case b'MAP_':  # Subheader (HEAD, DATA, NAME, PATH, VARS, ACTI)
                    subheader.chunk = MAP_(self.chkfmap); subheader.chunk.parse(io)
                case b'CELS':  # Subheader (GEOM, GLGM, GCGM, CTEX, CATR, CANM)
                    subheader.chunk = CELS(self.chkfmap); subheader.chunk.parse(io)
                case b'GRUV':  # Length of DATA chunk's array
                    subheader.chunk = GRUV(self.chkfmap); subheader.chunk.parse(Header.make_subreader(io, n, subheader.offs, subheader.size, subheader.tid))
                case b'GEOM':  # Tool Geometry (little-endian)
                    subheader.chunk = GEOM(self.chkfmap); subheader.chunk.parse(Header.make_subreader(io, n, subheader.offs, subheader.size, subheader.tid))
                case b'GLGM':  # PC Geometry (little-endian)
                    subheader.chunk = GLGM(self.chkfmap); subheader.chunk.parse(Header.make_subreader(io, n, subheader.offs, subheader.size, subheader.tid))
                case b'GCGM':  # GameCube Geometry (big-endian)
                    subheader.chunk = GCGM(self.chkfmap); subheader.chunk.parse(Header.make_subreader(io, n, subheader.offs, subheader.size, subheader.tid))
                case b'CTEX':  # PC Textures(?) (PSXtexfile)
                    subheader.chunk = CTEX(self.chkfmap); subheader.chunk.parse(Header.make_subreader(io, n, subheader.offs, subheader.size, subheader.tid))
                case b'CATR':
                    subheader.chunk = CATR(self.chkfmap); subheader.chunk.parse(Header.make_subreader(io, n, subheader.offs, subheader.size, subheader.tid))
                case b'CANM':  # Prop Animations
                    subheader.chunk = CANM(self.chkfmap); subheader.chunk.parse(Header.make_subreader(io, n, subheader.offs, subheader.size, subheader.tid))
                case b'HEAD':  # "Header" (cell dimensions)
                    subheader.chunk = HEAD(self.chkfmap); subheader.chunk.parse(Header.make_subreader(io, n, subheader.offs, subheader.size, subheader.tid))
                case b'DATA':  # Cell population data
                    subheader.chunk = DATA(self.chkfmap); subheader.chunk.parse(Header.make_subreader(io, n, subheader.offs, subheader.size, subheader.tid))
                case b'NAME':  # Prop names
                    subheader.chunk = NAME(self.chkfmap); subheader.chunk.parse(Header.make_subreader(io, n, subheader.offs, subheader.size, subheader.tid))
                case b'PATH':  
                    subheader.chunk = PATH(self.chkfmap); subheader.chunk.parse(Header.make_subreader(io, n, subheader.offs, subheader.size, subheader.tid))
                case b'ACTI':  # Actor layout data
                    subheader.chunk = ACTI(self.chkfmap); subheader.chunk.parse(Header.make_subreader(io, n, subheader.offs, subheader.size, subheader.tid))
                case b'VARS':
                    subheader.chunk = VARS(self.chkfmap); subheader.chunk.parse(Header.make_subreader(io, n, subheader.offs, subheader.size, subheader.tid))
                case _:
                    raise CHKFMAPError("Unknown TID < {} >".format(tid.decode()))
    #
    
    def write(self, io: BinaryIO):
        filepos_base = io.tell()
        io.seek(filepos_base + 4 + 20 * len(self.subheaders))
        for subheader in self.subheaders:
            subheader.offs = io.tell() - filepos_base
            subheader.chunk.write(io)
            io.seek(align_up(io.tell(), 4))  # Chunks have padding to next multiple of four
            subheader.size = io.tell() - filepos_base - subheader.offs
        filepos_back = io.tell()
        io.seek(filepos_base)
        io.write(pack("<I", len(self.subheaders)))
        for subheader in self.subheaders:
            io.write(pack("<4s4s4sII", subheader.tid, subheader.cid, subheader.ver, subheader.offs, subheader.size))
        io.seek(filepos_back)
        
    #

    @staticmethod
    def make_subreader(io: BinaryIO, idx: int, offs: int, size: int, tid: bytes):
        print("//////////////////////////////////////////////////////")
        print("LoadChunk chunkIDX {:08x} offset {:08x} len {:08x} TID < {:s} > filepos:{:08x}".format(idx, offs, size, tid.decode(), io.tell()))
        print("//////////////////////////////////////////////////////")
        return make_subreader(io, size)
    #

    def at(self, tid: bytes):
        for subheader in self.subheaders:
            if subheader.tid == tid: return subheader.chunk
        raise IndexError("Chunk with TID {} not found".format(tid))
    #
#

class CHKFMAP(Header):
    def __init__(self):
        super().__init__(self)
    #

    def parse(self, io: BinaryIO):
        filemagic = read_exact(io, 8)
        assert filemagic == b'CHKFMAP_'
        super().parse(io)
    #

    def write(self, io: BinaryIO):
        io.write(b'CHKFMAP_')
        super().write(io)
    #
#

class MAP_(Header):
    pass
#

class CELS(Header):
    pass
#

class GRUV(Chunk):  # Size of DATA chunk's array (HEAD chunk x * y * z)
    def parse(self, io: BinaryIO):
        self.data_count = unpack("<I", read_exact(io, 4))[0]
        print("gruv: {:d}".format(self.data_count))
    #

    def write(self, io: BinaryIO):
        io.write(pack("<I", self.data_count))
    #

    def __eq__(self, other: GRUV) -> bool:
        return self.data_count == other.data_count
    #
#

class GEOM(Chunk):  # This chunk is idiotic.  Four copies of the prop list also found in the GLGM chunk??
    def parse(self, io: BinaryIO):
        self.unkflt, prop_list_0_size, prop_list_1_size, prop_list_2_size, prop_list_3_size, prop_list_0_base, prop_list_1_base, prop_list_2_base, prop_list_3_base = unpack("<fIIIIIIII", read_exact(io, 36))
        print("master unkflt: {}".format(self.unkflt))

        io.seek(prop_list_0_base)
        self.props_0 = PropList.parse('<', make_subreader(io, prop_list_0_size))
        
        io.seek(prop_list_1_base)
        self.props_1 = PropList.parse('<', make_subreader(io, prop_list_1_size))
        
        # Prop list 2 uses a different vertex format that is incomprehensible (approx. 131.6017 bytes per vertex??)
        io.seek(prop_list_2_base);
        self.props_2_raw = read_exact(io, prop_list_2_size)
        
        io.seek(prop_list_3_base)
        self.props_3 = PropList.parse('<', make_subreader(io, prop_list_3_size))
    #

    def write(self, io: BinaryIO):
        filepos_base = io.tell()
        io.seek(filepos_base + 36)

        prop_list_0_base = io.tell() - filepos_base
        self.props_0.write('<', io)
        prop_list_0_size = io.tell() - filepos_base - prop_list_0_base

        prop_list_1_base = io.tell() - filepos_base
        self.props_1.write('<', io)
        prop_list_1_size = io.tell() - filepos_base - prop_list_1_base

        prop_list_2_base = io.tell() - filepos_base
        io.write(self.props_2_raw)
        prop_list_2_size = io.tell() - filepos_base - prop_list_2_base

        prop_list_3_base = io.tell() - filepos_base
        self.props_3.write('<', io)
        prop_list_3_size = io.tell() - filepos_base - prop_list_3_base

        filepos_back = io.tell()
        io.seek(filepos_base)
        io.write(pack("<fIIIIIIII", self.unkflt, prop_list_0_size, prop_list_1_size, prop_list_2_size, prop_list_3_size, prop_list_0_base, prop_list_1_base, prop_list_2_base, prop_list_3_base))
        io.seek(filepos_back)
    #

    def __eq__(self, other: GEOM) -> bool:
        return self.unkflt == other.unkflt and self.props_0 == other.props_0 and self.props_1 == other.props_1 and self.props_2_raw == other.props_2_raw and self.props_3 == other.props_3
    #
#

class GLGM(Chunk):  # Little-Endian
    def parse(self, io: BinaryIO) -> None:
        self.props = PropList.parse('<', io)
    #

    def write(self, io: BinaryIO) -> None:
        self.props.write('<', io)
    #

    def __eq__(self, other: GLGM) -> bool:
        return self.props == other.props
    #
#

class GCGM(Chunk):  # Big-Endian
    def parse(self, io: BinaryIO) -> None:
        self.props = PropList.parse('>', io)
    #

    def write(self, io: BinaryIO) -> None:
        self.props.write('>', io)
    #

    def __eq__(self, other: GCGM) -> bool:
        return self.props == other.props
    #
#

class CTEX(Chunk):
    def parse(self, io: BinaryIO):
        self.textures = parse_psxtexfile(io)
    #

    def write(self, io: BinaryIO):
        write_psxtexfile(io, self.textures)
    #

    def __eq__(self, other: CTEX) -> bool:
        return self.textures == other.textures
    #
#

class CATR(Chunk):
    def parse(self, io: BinaryIO):
        count = unpack("<I", read_exact(io, 4))[0]
        print("CATR Count: {:d}".format(count))
        self.packet_lists = list[PacketList]()
        for _ in range(count):
            packet_list = PacketList.parse(io)
            self.packet_lists.append(packet_list)
    #

    def write(self, io: BinaryIO):
        io.write(pack("<I", len(self.packet_lists)))
        for packet_list in self.packet_lists:
            packet_list.write(io)
    #

    def __eq__(self, other: CATR) -> bool:
        return self.packet_lists == other.packet_lists
    #

    def json_dump(self):
        return [packet_list.json_dump() for packet_list in self.packet_lists]
    #

    def json_load(self, vals: list) -> PacketList:
        self.packet_lists = [PacketList.json_load(packetlist_vals) for packetlist_vals in vals]
    #
#

class CANM(Chunk):
    def parse(self, io: BinaryIO):
        count = unpack("<I", read_exact(io, 4))[0]
        print("CANM Count: {:d}".format(count))
        self.packet_lists = list[PacketList]()
        for i in range(count):
            packet_list = PacketList.parse(io)
            # Repeating packet type 3 is clearly animation data (Prop IDs).
            name = packet_list.at(1).rstrip(b'\0').decode(codepage)  # Message
            print("{:2d}   name: {:>20s}".format(i, name))
            self.packet_lists.append(packet_list)
    #

    def write(self, io: BinaryIO):
        io.write(pack("<I", len(self.packet_lists)))
        for packet_list in self.packet_lists:
            packet_list.write(io)
    #

    def __eq__(self, other: CANM) -> bool:
        return self.packet_lists == other.packet_lists
    #

    def json_dump(self):
        return [packet_list.json_dump() for packet_list in self.packet_lists]
    #

    def json_load(self, vals: list) -> PacketList:
        self.packet_lists = [PacketList.json_load(packetlist_vals) for packetlist_vals in vals]
    #
#

class HEAD(Chunk):
    def parse(self, io: BinaryIO):
        self.x, self.y, self.z = unpack("<III", read_exact(io, 12))
        print("///////////////////////////////////////////")
        print("mapsize {:d} {:d} {:d}".format(self.x, self.y, self.z))  # ERRATA: In-game, this is printed before the values are byteswapped.
    #

    def write(self, io: BinaryIO):
        io.write(pack("<III", self.x, self.y, self.z))
    #

    def __eq__(self, other: HEAD) -> bool:
        return self.x == other.x and self.y == other.y and self.z == other.z
    #
#

class DATA(Chunk):
    def parse(self, io: BinaryIO):
        count = self.chkfmap.at(b'GRUV').data_count
        self.data = unpack(f"<{count}I", read_exact(io, count * 4))
    #

    def write(self, io: BinaryIO):
        count = len(self.data)
        io.write(pack(f"<{count}I", *self.data))
    #

    def __eq__(self, other: DATA) -> bool:
        return self.data == other.data
    #
#

class NAME(Chunk):
    def parse(self, io: BinaryIO):
        count = unpack("<I", read_exact(io, 4))[0]
        strndx = unpack(f"<{count}I", read_exact(io, count * 4))
        base_offs = io.tell()
        self.names = list[bytes]()
        for offs in strndx:
            io.seek(base_offs + offs)
            self.names.append(read_c_string(io))
    #

    def write(self, io: BinaryIO):
        io.write(pack("<I", len(self.names)))
        offs = 0
        for name in self.names:
            io.write(pack("<I", offs))
            offs += len(name) + 1
        for name in self.names:
            io.write(name + b'\0');
    #

    def __eq__(self, other: NAME) -> bool:
        return self.names == other.names
    #
#

class PATH(Chunk):
    def parse(self, io: BinaryIO):
        count = unpack("<I", read_exact(io, 4))[0]
        print("PATH Count: {:d}".format(count))
        self.packet_lists = list[PacketList]()
        for i in range(count):
            packet_list = PacketList.parse(io)
            # Repeating packet type 3 is clearly animation data (Prop IDs).
            name = packet_list.at(1).rstrip(b'\0').decode(codepage)  # Message
            print("{:2d}   name: {:s}".format(i, name))
            self.packet_lists.append(packet_list)
    #

    def write(self, io: BinaryIO):
        io.write(pack("<I", len(self.packet_lists)))
        for packet_list in self.packet_lists:
            packet_list.write(io)
    #

    def __eq__(self, other: PATH) -> bool:
        return self.packet_lists == other.packet_lists
    #

    def json_dump(self):
        return [packet_list.json_dump() for packet_list in self.packet_lists]
    #

    def json_load(self, vals: list) -> PacketList:
        self.packet_lists = [PacketList.json_load(packetlist_vals) for packetlist_vals in vals]
    #
#

def actor_id_translation(id: int) -> int:  # The programmers at SCG were smoking crack.
    if id > 8191:
        return id - 8160
    if id > 12:
        return id - 4083
    return id
#

actor_names = (     None, "heartstun",      "tk",        None,        None,              "health",    "pickup",     "lives",
                 "key 1",     "key 2",   "key 3",     "key 4",     "key 5",             "monkey1",   "monkey2",   "monkey3",
               "monkey4",   "monkey5",     "hog",  "balloon1",  "balloon2",             "trunkle",     "clown",      "baby",
                  "rat1",      "rat2",    "spit",   "pelican",      "coin",            "tikihead",       "cop",     "snake",
                 "ENV 1",     "ENV 2",   "ENV 3",     "ENV 4",     "ENV 5",               "ENV 6",     "ENV 7",     "ENV 8",
                 "ENV 9",    "ENV 10",  "ENV 11",    "ENV 12",    "ENV 13",              "ENV 14",    "ENV 15",    "ENV 16",
                "ENV 17",    "ENV 18",  "ENV 19",    "ENV 20",    "peanut", "tikihead_projectile",     "Gem 1",     "Gem 2",
                 "Gem 3",     "Gem 4",   "Gem 5", "Balloon 1", "Balloon 2",           "Balloon 3", "Balloon 4", "Balloon 5",
               "Fruit 1",   "Fruit 2", "Fruit 3",   "Fruit 4",   "Fruit 5",                  None)

class ACTI(Chunk):
    def parse(self, io: BinaryIO, dbgprint: bool = True):
        count = unpack("<I", read_exact(io, 4))[0]
        print("Actor Count: {:d}".format(count))
        self.actors = list[PacketList]()
        for i in range(count):
            packet_list = PacketList.parse(io)
            self.actors.append(packet_list)

            state = unpack("<i", packet_list.at(0))[0]  # Initial state or actor variant
            x, y, z = unpack("<iii", packet_list.at(2))  # Coarse XYZ Pos
            message = packet_list.at(3).rstrip(b'\0').decode(codepage)  # Message
            id = unpack("<i", packet_list.at(4))[0]  # Actor ID
            if dbgprint: print("{:2d}   state: {:2d}   xyz: {:3d} {:3d} {:3d}   message: {:>20s}   id: {:4d}".format(i, state, x, y, z, message, id), end = "")
            if id > 0xEFFF:  # See 800054e4
                if dbgprint: print()
            else:
                translated_id = actor_id_translation(id)
                if dbgprint: print("   translated: {:2d} {:s}".format(translated_id, str(actor_names[translated_id])))
    #

    def write(self, io: BinaryIO):
        io.write(pack("<I", len(self.actors)))
        for packet_list in self.actors:
            packet_list.write(io)
    #

    def __eq__(self, other: ACTI) -> bool:
        return self.actors == other.actors
    #

    def json_dump(self):
        return [actor.json_dump() for actor in self.actors]
    #

    def json_load(self, vals: list) -> PacketList:
        self.actors = [PacketList.json_load(packetlist_vals) for packetlist_vals in vals]
    #
#

class VARS(Chunk):
    def parse(self, io: BinaryIO):
        self.packet_list = PacketList.parse(io)
    #

    def write(self, io: BinaryIO):
        self.packet_list.write(io)
    #

    def __eq__(self, other: VARS) -> bool:
        return self.packet_list == other.packet_list
    #

    def json_dump(self):
        return self.packet_list.json_dump()
    #

    def json_load(self, vals: list) -> PacketList:
        self.packet_list = [Packet.json_load(packet_vals) for packet_vals in vals]
    #
#
