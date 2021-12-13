# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER, HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ether
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import ipv6
from ryu.lib.packet import in_proto
from ryu.lib.packet import ether_types
from ryu import utils
from ryu.lib.packet import tcp

     # Slices 100 and 200 with their respective MAC addresses for TCP
slices_data = [(100,"00:00:00:00:00:11","00:00:00:00:00:12","00:00:00:00:00:13",), 
               (200,"00:00:00:00:00:14","00:00:00:00:00:15","00:00:00:00:00:16",),
             ]
# Slices 300 and 400 with their respective MAC addresses for ICMP
slices_data2 = [(300,"00:00:00:00:00:11","00:00:00:00:00:15","00:00:00:00:00:16",), 
               (400,"00:00:00:00:00:14","00:00:00:00:00:12","00:00:00:00:00:13",),
               
              ]
        
slices_data3 = [(500,"00:00:00:00:00:11","00:00:00:00:00:15","00:00:00:00:00:16","00:00:00:00:00:14","00:00:00:00:00:12","00:00:00:00:00:13",), 
               
              ]
              
# Slices 600 and 700 with their respective MAC addresses and TCP port 

slices_data4 = [(600,"00:00:00:00:00:11","00:00:00:00:00:12","00:00:00:00:00:13",80), 
               (700,"00:00:00:00:00:14","00:00:00:00:00:15","00:00:00:00:00:13",22),
             ]
               
slice_100=slices_data[0][1:]
slice_200=slices_data[1][1:]


class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        self.logger.info("switch:%s connected", dpid)

        # Adding a flow in the flow table with the help of this function.
    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

        # Any packet in messege comes to controller, is procressed within this function.
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        arp_pkt = pkt.get_protocol(arp.arp)
        dpid = format(datapath.id, "d").zfill(16)
        self.mac_to_port.setdefault(dpid, {})
        
        dst = eth.dst
        src = eth.src

        

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

            # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:


             # check IP Protocol and create a match for IP
            if eth.ethertype == ether_types.ETH_TYPE_IP:
                ip = pkt.get_protocol(ipv4.ipv4)
                srcip = ip.src
                dstip = ip.dst
                protocol = ip.proto
                # if ICMP Protocol
                if protocol == in_proto.IPPROTO_ICMP:
                    for net_slice in slices_data2:
                        slice_id = net_slice[0]     # extract the slice ID
                        net_slice = net_slice[1:]
                        if src in net_slice and dst in net_slice:
                            self.logger.info("dpid %s in eth%s out eth%s", dpid, in_port, out_port)
                            self.logger.info("Slice pair [%s, %s] in slice %i protocol %s", src, dst, slice_id,protocol)
                            match = parser.OFPMatch(in_port=in_port, eth_dst=eth.dst, eth_src=eth.src,eth_type=eth.ethertype,ip_proto=protocol)
                            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                                return
                            else:
                                self.add_flow(datapath, 1, match, actions)
                    else: # pair of MAC addresses are not in a slice so skip 
                        return
                # if TCP Protocol
                if protocol == in_proto.IPPROTO_TCP:
                    _tcp = pkt.get_protocol(tcp.tcp)
                    dst_port = _tcp.dst_port
                    src_port = _tcp.src_port
                    for net_slice in slices_data4:
                        slice_id = net_slice[0]     # extract the slice ID
                        net_slice = net_slice[1:]
                        #Logic of slicing over TCP port
                        if src in net_slice and dst in net_slice and (dst_port in net_slice or src_port in net_slice):
                            self.logger.info("dpid %s in eth%s out eth%s", dpid, in_port, out_port)
                            self.logger.info("Slice pair [%s, %s] in slice %i protocol %s dst_port %s", src, dst, slice_id,protocol, dst_port)
                            match = parser.OFPMatch(in_port=in_port, eth_dst=eth.dst, eth_src=eth.src,eth_type=ether_types.ETH_TYPE_IP, ip_proto=protocol,tcp_src= src_port, tcp_dst= dst_port )
                            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                                return
                            else:
                                self.add_flow(datapath, 1, match, actions)
                    else: # pair of MAC addresses are not in a slice so skip 
                        return
                else:
                        for net_slice in slices_data3:
                            slice_id = net_slice[0]     # extract the slice ID
                            net_slice = net_slice[1:]
                            if src in net_slice and dst in net_slice:
                                self.logger.info("dpid %s in eth%s out eth%s", dpid, in_port, out_port)
                                self.logger.info("Slice pair [%s, %s] in slice %i", src, dst, slice_id)
                                match = parser.OFPMatch(in_port=in_port, eth_dst=eth.dst, eth_src=eth.src,eth_type=eth.ethertype)
                                if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                                    self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                                    return
                                else:
                                    self.add_flow(datapath, 1, match, actions)
                        else: # pair of MAC addresses are not in a slice so skip 
                            return
        # Packet out messege building by the controller.        
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
       