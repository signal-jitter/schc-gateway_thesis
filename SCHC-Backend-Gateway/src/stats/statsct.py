"""
statsct.py: Statistics Collector for openSCHC
Collects data related to: number of fragments in tx and rx, time on air, number of bytes per fragment
window size, tile size, size of the acks
Centralize the information for analysis
The stats are write to a file
"""
#import collections.defaultdict as defaultdict

try:
    from ucollections import defaultdict
except ImportError:
    from collections import defaultdict


try:
    from ucollections import OrderedDict
except ImportError:
    from collections import OrderedDict

try:
    import utime as time
except ImportError:
    import time
    
import sys
from .toa_calculator import get_toa
import frag_msg
from gen_utils import dprint, dpprint


sys.path.append("..")
from gen_base_import import *  # used for now for differing modules in py/upy
from gen_utils import dprint, dpprint

#from ..bitarray import BitBuffer
SCHC_FRAG = "SCHC_FRAG"
SCHC_ACK_OK = "SCHC_ACK_OK"
SCHC_ACK_KO = "SCHC_ACK_KO"
SCHC_SENDER_ABORT = "SCHC_SENDER_ABORT"
SCHC_RECEIVER_ABORT = "SCHC_RECEIVER_ABORT"
SCHC_ALL_1 = "SCHC_ALL_1" 


class Statsct(object):
    src_id = None
    dst_id = None
    results = OrderedDict()
    sender_packets = OrderedDict()
    receiver_packets = OrderedDict()
    SF = 8
    dc = 1
    device_rule = dict()
    gw_rule = dict()
    channel_occupancy = 0
    goodput = 0
    total_delay = 0
    reliability = 0
    packet_info = dict()
    total_packet_send = dict()
    total_data_send = 0
    #msg_type: "SCHC_FRAG", "SCHC_ACK", "SCHC_SENDER_ABORT", "SCHC_RECEIVER_ABORT"
    msg_type = ""
    packet_length = 0
    succ_packets = 0
    fail_packets = 0
    last_msg_type = ''
    msg_type_queue = []
    channel_occupancy_sender = 0
    channel_occupancy_receiver = 0
    background_traffic = None
    position = None
    current_time = None
    @staticmethod
    def initialize(init_time=None):
        """Class to initializa the static class
        creates the file to write and the instance of the class """
        dprint('Init statsct module')
        if init_time is None:
            init_time = time.time() # XXX: need refactor, should be obtained from Scheduler
        Statsct.results['init_time'] = init_time #utime.time() -->exception
        Statsct.results['packet_list'] = []
        Statsct.sender_packets['packet_list'] = []
        Statsct.receiver_packets['packet_list'] = []
        Statsct.src_id = None
        Statsct.dst_id = None
        Statsct.device_rule = dict()
        Statsct.gw_rule = dict()
        Statsct.gw_rule['fragSender'] = []
        Statsct.channel_occupancy = 0
        Statsct.goodput = 0
        Statsct.total_delay = 0
        Statsct.reliability = 0
        Statsct.total_packet_send = dict()
        Statsct.msg_type = ""
        Statsct.packet_info = dict()
        Statsct.last_msg_type = ""
        Statsct.succ_packets = 0
        Statsct.fail_packets = 0
        Statsct.total_data_send = 0
        Statsct.msg_type_queue = []
        Statsct.channel_occupancy_sender = 0
        Statsct.channel_occupancy_receiver = 0
    @staticmethod
    def set_background_traffic(background_traffic):
        Statsct.background_traffic = background_traffic
    @staticmethod
    def get_background_traffic():
        return Statsct.background_traffic
    @staticmethod
    def set_current_time(current_time):
        Statsct.current_time = current_time
    @staticmethod
    def get_current_time():
        return Statsct.current_time
    @staticmethod
    def set_position(position):
        Statsct.position = position
    @staticmethod
    def get_position():
        return Statsct.position
        
    @staticmethod
    def set_packet_size(packet_length):
        Statsct.packet_length = packet_length
    @staticmethod
    def get_results():
        return {"results":Statsct.results,
                "sender":Statsct.sender_packets,
                "receiver":Statsct.receiver_packets
                }
    @staticmethod
    def set_msg_type(schc_msg_type):
        Statsct.msg_type = schc_msg_type
        #Statsct.packet_info['msg_type'] = schc_msg_type
        Statsct.msg_type_queue.append(schc_msg_type)
        dprint("msg_type -> {}, msg_queue -> {}".format(Statsct.msg_type, Statsct.msg_type_queue))
        # input("")


    @staticmethod
    def set_header_size(header_size):
        Statsct.packet_info['header_size'] = header_size
        dprint("header_size -> {}".format(Statsct.packet_info))
        #input("header size")

    @staticmethod
    def log(message):
        dprint("[statsct] {}".format(message))
        
    @staticmethod
    def set_SF(SF):
        Statsct.SF = SF

    @staticmethod
    def set_device_rule(rule):
        Statsct.device_rule = rule
        Statsct.log('rule configure device -> {}'.format(Statsct.device_rule))

    @staticmethod
    def set_gw_rule(rule):
        Statsct.gw_rule = rule
        Statsct.log('rule configure gw -> {}'.format(Statsct.gw_rule))

    @staticmethod
    def setSourceAddress(schcSenderAddress):
        """Set the source address in the results dict
        :param schcSenderAddress: Address of the sender """
        Statsct.src_id = schcSenderAddress
        Statsct.log("src_id -> {}".format(Statsct.src_id))
        Statsct.results['src_id'] = Statsct.src_id
        #dprint(str(Statsct.results))

    @staticmethod
    def setDestinationAddress(schcDestinationAddress):
        """Set the destination address in the results dict
        :param schcDestinationAddress: Address of the receiver"""
        Statsct.dst_id = schcDestinationAddress
        Statsct.log("dst_id -> {}".format(Statsct.dst_id))
        Statsct.results['dst_id'] = Statsct.dst_id 
        #dprint(str(Statsct.results))
 

    @staticmethod    
    def addInfo(key, value):
        Statsct.log("{}, {}".format(key,value))
        Statsct.results[key] = value
        #dprint(str(Statsct.results))
        

    @staticmethod
    def print_results():
        Statsct.log("Results")
        for key in Statsct.results:
            Statsct.log("{}, {}".format(key,Statsct.results[key]))
        Statsct.log("sender_packets")
        for key in Statsct.sender_packets:
            Statsct.log("{}, {}".format(key,Statsct.sender_packets[key]))
        Statsct.log("receiver_packets")
        for key in Statsct.receiver_packets:
            Statsct.log("{}, {}".format(key,Statsct.receiver_packets[key]))
    
    @staticmethod
    def add_packet_info(clock, packet,src_dev_id,dst_dev_id, status):
        """ Add the information of the packet to the results dict 
        :param packet: packet send
        :param src_dev_id: device source id
        :param dst_dev_id: device destination id
        :param status: if the message was send successful (True) or not (False) """
        Statsct.packet_info['time'] = clock # time.time() # utime.time()
        Statsct.packet_info['src_dev_id'] = src_dev_id
        Statsct.packet_info['dst_dev_id'] = dst_dev_id
        Statsct.packet_info['packet'] = packet
        Statsct.packet_info['status'] = status
        Statsct.packet_info['packet_length'] = len(packet)

        Statsct.set_total_data_send(Statsct.packet_info['packet_length'])

        Statsct.packet_info['toa_calculator'] = get_toa(len(packet), Statsct.SF)
        Statsct.packet_info['toa_packet'] = Statsct.packet_info['toa_calculator']['t_packet']
        Statsct.packet_info['time_off'] = Statsct.dc_time_off(Statsct.packet_info['toa_packet'],Statsct.dc) 
        Statsct.log(Statsct.packet_info)
        Statsct.packet_info['msg_type'] =''
        if len(Statsct.msg_type_queue) != 0:
            Statsct.packet_info['msg_type'] = Statsct.msg_type_queue.pop(0)
            dprint(Statsct.packet_info['msg_type'])
            dprint("msg_type_queue -> {}".format(Statsct.msg_type_queue))
            #input('')
        else:
            dprint("all elements should have a msg_type")
            #input('')
        # if 'msg_type' not in Statsct.packet_info:
        #     dprint("No message type found, asuming retx")

        #     #Statsct.packet_info['msg_type'] = Statsct.last_msg_type
        #     Statsct.packet_info['msg_type'] = ''

        # else:
        #     Statsct.last_msg_type = Statsct.packet_info['msg_type']    
       
        Statsct.results['packet_list'].append(Statsct.packet_info)
        #dprint('Statsct.results: ',Statsct.results)
        #calculate performace metrics
        Statsct.addChannelOccupancy(Statsct.packet_info['toa_packet'])
        #Statsct.log(str(Statsct.results))
        dprint("src_dev_id {} , Statsct.src_id {}".format(src_dev_id,Statsct.src_id))

        if src_dev_id == Statsct.src_id:
            Statsct.sender_packets['packet_list'].append(Statsct.packet_info)
            # Statsct.get_msg_type(packet, Statsct.device_rule['fragSender'])
            Statsct.get_msg_type(packet, Statsct.device_rule)
            Statsct.channel_occupancy_sender += Statsct.packet_info['toa_packet']

            dprint("packet added to sender list")
            #Statsct.log(Statsct.sender_packets)
        else:
            Statsct.receiver_packets['packet_list'].append(Statsct.packet_info)
            # Statsct.get_msg_type(packet, Statsct.gw_rule['fragSender'])
            Statsct.get_msg_type(packet, Statsct.gw_rule)
            Statsct.channel_occupancy_receiver += Statsct.packet_info['toa_packet']
            
            dprint("packet added to receiver list")
            #Statsct.log(Statsct.receiver_packets)
        #input('')
        #calcute the time off of each packet
        # if Statsct.packet_info['msg_type'] == '':
        #     Statsct.packet_info['msg_type'] = Statsct.last_msg_type
        # else:    
        #     Statsct.last_msg_type = Statsct.packet_info['msg_type']
        Statsct.packet_info = dict()
    @staticmethod
    def calculate_tx_parameters():
        """ Calculates the parameters of the transmission
        Parameters:
        ToA uplink & downlink
        number of packets uplink & downlink
        goodput of the transmission -> packet size / total data send 
        reliability # of data packets / received 
        """
        dprint('print_ordered_fragments')
        for i,k in enumerate(Statsct.results['packet_list']):
            
            if "status" in k:
                if k['status']:
                    Statsct.succ_packets +=1
                else:
                    Statsct.fail_packets +=1
        nb_packet = (Statsct.fail_packets + Statsct.succ_packets)
        ratio = Statsct.succ_packets / max(nb_packet, 1)
            #dprint('{},toa_packet: {},status: {}, packet_length:{}, msg_type: {}'.format(i,k['toa_packet'], k['status'],k['packet_length'],k['msg_type']))
        packet_status = None
        for k in Statsct.results['packet_list']:
            if "msg_type" in k:
                if k['msg_type'] == SCHC_RECEIVER_ABORT or k['msg_type'] == SCHC_SENDER_ABORT:
                    packet_status = False
                else:
                    packet_status = True
        total_time_off = 0
        total_delay = 0
        sender_toa = 0
        time_off_last_send_frag = 0
        for i,k in enumerate(Statsct.sender_packets['packet_list']):
            if "time_off" in k:
                if i != (len(Statsct.sender_packets['packet_list']) - 1):
                    total_time_off += k['time_off']
                else:
                    time_off_last_send_frag = k['time_off']
            if "toa_packet" in k:

                sender_toa += k['toa_packet']
        
        dprint("total_time_off -> {}, sender_toa -> {}".format(total_time_off,sender_toa))
        
        total_time_off_receiver = 0
        receiver_toa = 0
        toa_last_receiver_frag = 0
        for i,k in enumerate(Statsct.receiver_packets['packet_list']):
            if "time_off" in k:
                if i != (len(Statsct.receiver_packets['packet_list']) - 1):
                    total_time_off_receiver += k['time_off']
            if "toa_packet" in k:
                if i == (len(Statsct.receiver_packets['packet_list'])):
                    toa_last_receiver_frag = k['toa_packet']
                    dprint("toa_last_receiver_frag -> {}".format(toa_last_receiver_frag))
                    input("")
                receiver_toa += k['toa_packet']
        
        
        ACK_OK_TOA = 0
        RECEIVER_ABORT_TOA = 0
        ACK_KO_TOA = 0
        for k in Statsct.results['packet_list']:
            if "msg_type" in k:
                if k['msg_type'] == SCHC_ACK_OK:
                    assert 'toa_packet' in k
                    ACK_OK_TOA = k['toa_packet']
                elif k['msg_type'] == SCHC_RECEIVER_ABORT:
                    assert 'toa_packet' in k
                    RECEIVER_ABORT_TOA = k['toa_packet'] 
                elif k['msg_type'] == SCHC_ACK_KO:
                    assert 'toa_packet' in k
                    ACK_KO_TOA += k['toa_packet']
        dprint("ACK_OK_TOA: {}, ACK_KO_TOA: {}, RECEIVER_ABORT_TOA: {} => Total GW Time: {}".format(
                    ACK_OK_TOA, ACK_KO_TOA,RECEIVER_ABORT_TOA, ACK_OK_TOA + RECEIVER_ABORT_TOA))     
        dprint("total_time_off_receiver -> {} receiver_toa -> {}".format(total_time_off_receiver,receiver_toa))
        #input('')
        total_delay = sender_toa + total_time_off + ACK_OK_TOA + RECEIVER_ABORT_TOA
        total_delay_app = sender_toa + total_time_off
        
        dprint("Channel Ocuppancy -> {}".format(Statsct.channel_occupancy))
        dprint("total_data_send -> {}, packet_length -> {}".format(Statsct.total_data_send,Statsct.packet_length))
        
        goodput = Statsct.packet_length / max(Statsct.total_data_send, 1)

        return {"channel_occupancy":Statsct.channel_occupancy,
                "goodput":goodput, "ratio": ratio, "succ_fragments": Statsct.succ_packets,
                "fail_fragments":Statsct.fail_packets, "packet_status":packet_status,
                "total_delay":total_delay, "channel_occupancy_sender":Statsct.channel_occupancy_sender,
                "channel_occupancy_receiver":Statsct.channel_occupancy_receiver,
                 "total_data_send":Statsct.total_data_send, "packet_length":Statsct.packet_length,
                 "total_time_off":total_time_off, "sender_toa":sender_toa,
                 "total_time_off_receiver":total_time_off_receiver, 
                 "toa_last_receiver_frag":toa_last_receiver_frag,
                 "receiver_toa":receiver_toa,
                 "total_delay_app":total_delay_app
                  }

    @staticmethod
    def addChannelOccupancy(toa):
        Statsct.channel_occupancy += toa
        dprint("channel_occupancy -> {}".format(Statsct.channel_occupancy))

    @staticmethod
    def set_total_data_send(data):
        Statsct.total_data_send += data
        dprint("total_data_send -> {}".format(Statsct.total_data_send))

    @staticmethod
    def addGoodput():
        Statsct.goodput += Statsct.goodput
    
    @staticmethod
    def addTotalDelay(time):
        Statsct.total_delay += time
        dprint("total_delay -> {}".format(Statsct.total_delay))
    
    @staticmethod
    def addReliability():
        Statsct.reliability += Statsct.reliability



    

    @staticmethod
    def get_msg_type(payload, rule):
        """ 
        dprint("get message type -> {}, rule -> {}".format(payload, rule))
        
        packet_bbuf = BitBuffer(payload)
        dprint(packet_bbuf)
        try:
            schc_frag = schcmsg.frag_receiver_rx(rule, packet_bbuf)
            dprint(schc_frag.__dict__)
            if 'packet_bbuf' in schc_frag.__dict__:
                dprint("packet_bbuf len-> {}".format(schc_frag.__dict__['packet_bbuf']))
                #input('frag_receiver_rx')

            return schc_frag.__dict__
        except Exception as e:
            dprint(e)
        dprint("rule:{}".format(rule))
        
        
        packet_bbuf = BitBuffer(payload)
        dprint(packet_bbuf)
        try:
            schc_frag = schcmsg.frag_sender_rx(rule, packet_bbuf)
            dprint(schc_frag.__dict__)
            #input('frag_sender_rx')
            return schc_frag.__dict__
        except Exception as e:
            dprint(e)
        # try:
        #     schc_frag_2 = schcmsg.frag_sender_rx(Statsct.device_rule['fragReceiver'], packet_bbuf)
        #     dprint(schc_frag_2.__dict__)
        # except Exception as e:
        #     dprint(e)
        # try:
        #     schc_frag_2 = schcmsg.frag_sender_rx(Statsct.device_rule['fragReceiver'], packet_bbuf)
        #     dprint(schc_frag_2.__dict__)
        # except Exception as e:
        #     dprint(e)
        #input('')

        """
    @staticmethod
    def dc_time_off(time_on,dc):
        """Calculates the time off for a given duty cycle 
        :param dc: duty cycle
        :param time_on: time on air, active time
        :returns time_off: time off required after transmission
        """
        time_off = time_on * ((100-dc)/dc)
        return time_off
    
    @staticmethod
    def print_packet_list(packet_list):
        """Prints the info of each packet """
        dprint('print_packet_list ')
        for i,k in enumerate(packet_list['packet_list']):
            dprint('{},{}'.format(i,k))

    @staticmethod
    def print_ordered_packets():
        dprint('print_ordered_packets ')
        for i,k in enumerate(Statsct.results['packet_list']):
            dprint('{}:{}:,source:{},toa_packet: {}, time off: {},status: {}, packet_length:{}, msg_type: {}'.format(i,k['time'],k['src_dev_id'],k['toa_packet'],k['time_off'], k['status'],k['packet_length'],k['msg_type']))
        
        



    # @staticmethod
    # def log(self, name, message):
    #     self.system.log(name, message)
    """
    @staticmethod
    def add_packet_info_type(packet,src_dev_id,dst_dev_id, status, msg_type):
        Add the information of the packet to the results dict 
        :param packet: packet send
        :param src_dev_id: device source id
        :param dst_dev_id: device destination id
        :param status: if the message was send successful (True) or not (False) 
        :param msg_type: message type (fragment, sender-abort, receiver-abort, all-1
        packet_info = dict()
        packet_info['time'] = utime.time()
        packet_info['src_dev_id'] = src_dev_id
        packet_info['dst_dev_id'] = dst_dev_id
        packet_info['packet'] = packet
        packet_info['status'] = status
        packet_info['msg_type'] = msg_type
        packet_info['packet_length'] = len(packet)
        packet_info['toa_calculator'] = get_toa(len(packet), Statsct.SF)
        packet_info['toa_packet'] = packet_info['toa_calculator']['t_packet']
        packet_info['time_off'] = Statsct.dc_time_off(packet_info['toa_packet'],Statsct.dc) 
        Statsct.log(packet_info)
        Statsct.results['packet_list'].append(packet_info)
        #Statsct.log(str(Statsct.results))
        if src_dev_id == Statsct.src_id:
            Statsct.sender_packets['packet_list'].append(packet_info)
            
            #Statsct.log(Statsct.sender_packets)
        else:
            Statsct.receiver_packets['packet_list'].append(packet_info)
            #Statsct.log(Statsct.receiver_packets)
        #calcute the time off of each packet
    """
