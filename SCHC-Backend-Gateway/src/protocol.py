"""
.. module:: schc
   :platform: Python, Micropython
"""
# ---------------------------------------------------------------------------

from gen_base_import import *  # used for now for differing modules in py/upy
from gen_utils import dprint, dpprint, set_debug_output

# ---------------------------------------------------------------------------

from frag_recv import ReassemblerAckOnError
from frag_recv import ReassemblerNoAck
from frag_send import FragmentAckOnError
from frag_send import FragmentNoAck
import frag_msg
from compr_parser import *
from compr_core import Compressor, Decompressor

from gen_utils import dtrace
import binascii


# ---------------------------------------------------------------------------

class SessionManager:
    """Maintain the table of active fragmentation/reassembly sessions.

    Internals:
       session_table[(l2_address, rule_id, rule_id_size, dtag)]
              -> session

    When 'unique_peer' is true, the l2_address for another peer is 'None'.
    """

    def __init__(self, protocol, unique_peer):
        self.protocol = protocol
        self.unique_peer = unique_peer
        self.session_table = {}

    def _filter_session_id(self, session_id):
        if self.unique_peer:
            session_id = (None,) + session_id[1:]
        return session_id

    def find_session(self, session_id):
        session_id = self._filter_session_id(session_id)
        session = self.session_table.get(session_id, None)
        return session

    def _add_session(self, session_id, session):
        session_id = self._filter_session_id(session_id)
        assert session_id not in self.session_table
        self.session_table[session_id] = session

    def delete_session(self, session_id):
        self.session_table.pop(session_id)
        dprint("SessionManager: deleted", session_id)

    def create_reassembly_session(self, context, rule, session_id):
        session_id = self._filter_session_id(session_id)
        l2_address, rule_id, unused, dtag = session_id
        if self.unique_peer:
            l2_address = None
        mode = rule[T_FRAG][T_FRAG_MODE]
        if mode == T_FRAG_NO_ACK:
            session = ReassemblerNoAck(
                self.protocol, context, rule, dtag, l2_address)
        elif mode == T_FRAG_ACK_ALWAYS:
            raise NotImplementedError("FRMode:", mode)
        elif mode == T_FRAG_ACK_ON_ERROR:
            session = ReassemblerAckOnError(
                self.protocol, context, rule, dtag, l2_address)
        else:
            raise ValueError("FRMode:", mode)
        self._add_session(session_id, session)
        setattr(session, "_session_id", session_id)
        return session

    def create_fragmentation_session(self, l2_address, context, rule):
        if self.unique_peer:
            l2_address = None

        rule_id = rule[T_RULEID]
        rule_id_length = rule[T_RULEIDLENGTH]
        dtag_length = rule[T_FRAG][T_FRAG_PROF][T_FRAG_DTAG]
        dtag_limit = 2 ** dtag_length

        for dtag in range(0, dtag_limit):
            session_id = (l2_address, rule_id, rule_id_length, dtag)
            session_id = self._filter_session_id(session_id)
            if session_id not in self.session_table:
                break

        if dtag == dtag_limit:
            self.protocol.log("cannot create session, no dtag available")
            return None

        mode = rule[T_FRAG][T_FRAG_MODE]
        if mode == T_FRAG_NO_ACK:
            session = FragmentNoAck(self.protocol, context, rule, dtag)
        elif mode == T_FRAG_ACK_ALWAYS:
            raise NotImplementedError(
                "{} is not implemented yet.".format(mode))
        elif mode == T_FRAG_ACK_ON_ERROR:
            session = FragmentAckOnError(self.protocol, context, rule, dtag)
        else:
            raise ValueError("invalid FRMode: {}".format(mode))
        self._add_session(session_id, session)
        setattr(session, "_session_id", session_id)
        return session

    def get_state_info(self, **kw):
        return [(session_id, session.get_state_info(**kw))
                for (session_id, session) in self.session_table.items()]


# ---------------------------------------------------------------------------

class SCHCProtocol:
    """This class is the entry point for the openschc
    (in this current form, object composition is used)

    """

    def __init__(self, config, system, layer2, layer3, role, unique_peer):
        assert role in ["device", "core-server"]
        self.config = config
        self.unique_peer = unique_peer
        self.role = role
        self.system = system
        self.scheduler = system.get_scheduler()
        self.layer2 = layer2
        self.layer3 = layer3
        self.layer2._set_protocol(self)
        self.layer3._set_protocol(self)
        self.compressor = Compressor(self)
        self.decompressor = Decompressor(self)
        self.session_manager = SessionManager(self, unique_peer)
        if ((isinstance(config, object) and hasattr(config, "debug_level")) or
                (isinstance(config, dict) and config.get("debug_level", 0))):
            set_debug_output(True)

    def _log(self, message):
        self.log("schc", message)

    def log(self, name, message):
        self.system.log(name, message)

    def set_rulemanager(self, rule_manager):
        self.rule_manager = rule_manager

    def get_system(self):
        return self.system

    def _apply_compression(self, dst_l3_address, raw_packet):
        """Apply matching compression rule if one exists.
        
        In any case return a SCHC packet (compressed or not) as a BitBuffer
        """
        context = self.rule_manager.find_context_bydstiid(dst_l3_address)
        if self.role == "device":
            t_dir = T_DIR_UP
        else:
            assert self.role == "core-server"
            t_dir = T_DIR_DW

        # Parse packet as IP packet and apply compression rule
        P = Parser(self)
        parsed_packet, residue, parsing_error = P.parse(raw_packet, t_dir)
        self._log("parser {} {} {}".format(parsed_packet, residue, parsing_error))
        if parsed_packet is None:
            return BitBuffer(raw_packet)

        # Apply compression rule
        rule, dev_id = self.rule_manager.FindRuleFromPacket(parsed_packet, direction=t_dir)
        self._log("compression rule {}".format(rule))
        if rule is None:
            rule = self.rule_manager.FindNoCompressionRule(dst_l3_address)
            self._log("no-compression rule {}".format(rule))

        if rule is None:
            # XXX: not putting any SCHC compression header? - need fix
            self._log("rule for compression/no-compression not found")
            return BitBuffer(raw_packet)

        if rule["Compression"] == []:  # XXX: should be "NoCompression"
            self._log("compression result no-compression")
            return BitBuffer(raw_packet)

        schc_packet, rule_port = self.compressor.compress(rule, parsed_packet, residue, t_dir)
        dprint(schc_packet)
        schc_packet.display("bin")
        self._log("compression result {}".format(schc_packet))

        return schc_packet, rule_port

    def _make_frag_session(self, dst_l2_address, direction):
        """Search a fragmentation rule, create a session for it, return None if not found"""
        frag_rule = self.rule_manager.FindFragmentationRule(
            deviceID=dst_l2_address, direction=direction)
        if frag_rule is None:
            self._log("fragmentation rule not found")
            return None

        # Perform fragmentation
        rule = frag_rule
        context = None  # LT: don't know why context is needed, should be self.rule_manager which handle the context
        self._log("fragmentation rule_id={}".format(rule[T_RULEID]))

        session = self.session_manager.create_fragmentation_session(
            dst_l2_address, context, rule)
        if session is None:
            self._log("fragmentation session could not be created")  # XXX warning
            return None

        return session

    def schc_send(self, dst_l2_address, dst_l3_address, raw_packet):
        """Starting to send SCHC packet after called by L3.
        
        If dst_l2_address is None, this function is for sending
        from device to core.

        XXX the order of the args should be:
            schc_send(self, dst_l3_address, raw_packet, dst_l2_address=None)
        """
        self._log("recv-from-l3 {} {} {}".format(dst_l2_address, dst_l3_address, raw_packet))

        # Perform compression
        packet_bbuf, rule_port = self._apply_compression(dst_l3_address, raw_packet)

        # Check if fragmentation is needed.
        print("FRAG ???")
        print(packet_bbuf.count_added_bits())
        print(self.layer2.get_mtu_size())
        if packet_bbuf.count_added_bits() < self.layer2.get_mtu_size():
            self._log("fragmentation not needed size={}".format(
                packet_bbuf.count_added_bits()))
            #self.scheduler.add_event(0, self.layer2.send_packet, args)  # XXX: what about directly send?
            self.layer2.send_packet(packet_bbuf.get_content(), rule_port, dst_l2_address)
            return

        # Start a fragmentation session from rule database
        if dst_l2_address == None:
            direction = T_DIR_UP
        else:
            direction = T_DIR_DW
        frag_session = self._make_frag_session(dst_l2_address, direction)
        if frag_session is not None:
            ###Re-applying Rule ID to Buffer for fragmentation
            print("Re-applying Rule-ID to the Buffer for fragmentation (protocol.py - l 252)")
            packet_bbuf.add_bytes(rule_port, 0)
            frag_session.set_packet(packet_bbuf)
            frag_session.start_sending()

    def schc_recv(self, dst_l2_addr, raw_packet, rule_port):
        """Receiving a SCHC packet from a lower layer."""
        print(raw_packet) #############################################################################DELETE
        packet_bbuf = BitBuffer(raw_packet)
        dprint('SCHC: recv from L2:', b2hex(packet_bbuf.get_content()), "on Port: ", rule_port)
        frag_rule = self.rule_manager.FindFragmentationRule(
            deviceID=dst_l2_addr, packet=packet_bbuf)

        dtrace('\t\t\t-----------{:3}--------->|'.format(len(packet_bbuf._content)))
        if frag_rule is None:
            print("SKIP Fragmentation - no Frag MODE")
            self.process_decompress(packet_bbuf, dst_l2_addr, rule_port, "UP")
        else:
            dtag_length = frag_rule[T_FRAG][T_FRAG_PROF][T_FRAG_DTAG]
            if dtag_length > 0:
                dtag = packet_bbuf.get_bits(dtag_length, position=frag_rule[T_RULEIDLENGTH])
            else:
                dtag = None  # XXX: get_bits(0) should work?

            rule_id = frag_rule[T_RULEID]
            rule_id_length = frag_rule[T_RULEIDLENGTH]
            session_id = (dst_l2_addr, rule_id, rule_id_length, dtag)
            session = self.session_manager.find_session(session_id)

            if session is not None:
                dprint("{} session found".format(
                    session.get_session_type().capitalize()),
                    session.__class__.__name__)
            else:
                context = None
                session = self.session_manager.create_reassembly_session(
                    context, frag_rule, session_id)
                dprint("New reassembly session created", session.__class__.__name__)

            session.receive_frag(packet_bbuf, dtag)

    def process_decompress(self, packet_bbuf, dev_l2_addr, rule_port, direction):
        print("BUFFFFFFFFFFFFFFER111111:")
        print(packet_bbuf._rpos)
        ###
        #rule = self.rule_manager.FindRuleFromSCHCpacket(packet_bbuf, dev_l2_addr)
        rule = self.rule_manager.FindRuleFromID(rule_port, dev_l2_addr)
        print(rule)
        if rule is None:
            # reject it.
            self._log("No compression rule for SCHC packet, sender L2addr={}"
                      .format(dev_l2_addr))
            self.scheduler.add_event(0, self.layer3.recv_packet,
                                     (dev_l2_addr, packet_bbuf.get_content()))
            return

        if "Compression" not in rule:
            # reject it.
            self._log("Not compression parameters for SCHC packet, sender L2addr={}".format(
                dev_l2_addr))
            return

        if rule["Compression"]:
            dprint("---------------------- Decompression ----------------------")
            dprint("---------------------- Decompression Rule-------------------------")
            self._log("compression rule_id={}".format(rule[T_RULEID]))
            dprint("receiver frag received:", packet_bbuf)
            dprint('rule {}'.format(rule))
            dprint("------------------------ Decompression ---------------------------")
            raw_packet = self.decompressor.decompress(packet_bbuf, rule, direction)
            dprint("---- Decompression result ----")
            dprint(raw_packet)
            #args = (dev_l2_addr, raw_packet)
            #self.scheduler.add_event(0, self.layer3.recv_packet, args)

            payload_bin = packet_bbuf.get_content()

            payload = binascii.hexlify(payload_bin).decode('ascii')
            print("Payload:")
            print(payload)
            self.layer3.recv_packet(dev_l2_addr, raw_packet, payload[1:])

    # def process_decompress(self, context, dev_l2_addr, schc_packet):
    #    self._log("compression rule_id={}".format(context["comp"]["ruleID"]))
    #    raw_packet = self.decompressor.decompress(context, schc_packet)
    #    args = (dev_l2_addr, raw_packet)
    #    self.scheduler.add_event(0, self.layer3.recv_packet, args)

    def get_state_info(self, **kw):
        result = {
            "sessions": self.session_manager.get_state_info(**kw)
        }
        return result

    def get_init_info(self, **kw):
        result = {
            "role": self.role,
            "unique-peer": self.unique_peer
        }
        result["rule-manager"] = self.rule_manager.get_init_info(**kw)
        return result
