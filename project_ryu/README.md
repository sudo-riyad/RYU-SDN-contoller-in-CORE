# Netowrk Slicing in CORE

## This is the implemetation and documentation for implenemting Network Slicing through RYU SDN controller in SDN data plane in CORE emulator for Master project

### The followings is the architectural overview of SDN network implementation

In this approach, the experimental goal is to make a multitenant sliced network. In this regards, nine Open
vSwitches (OVS) are used to build the SDN data plane network. Figure  presents the topology for implementing the 1st approach which is done in CORE emulator.

![ryu_controller](https://user-images.githubusercontent.com/57096728/145966629-8413c97c-ff06-4f29-b9f3-116b2eb8193f.JPG)

In the network diagram, all the Open vSwitches are connected to a simple layer 2 physical switch from interface
eth0. The traditional switch is then connected with a RJ45 connector from CORE emulator to localhost of CORE
hosted machine. The RYU SDN controller running on the same virtual machine connects to the CORE emulated
physical devices.
The purpose of this topology is to make two slices using ICMP protocol, namely slice 300 and slice 400. Slice
300 consists of User1, User3 and Server2, while slice 400 comprises of User4, User2, Server1. Slice 300 devices can only able to reach each other through ICMP ping, which is totally independent from slice 400 devices.
This is also similarly applicable for slice 400. In addition, service based slices are also implemented on this experiment, and those slices are defined as slice 600 and slice 700. Two services, one is webservice with HTTP
port 80 and another SSH with port 22 are considered in this method. These services are sliced on the basis of
TCP protocol. Both of the services have been running on server1, but only one service which is in a specific slice
can be reached by tenant of that slice. As a result, slice 600 comprised of User1, User2 can get webservice
through TCP port 80 and on the other hand, slice 600 composed of User3, User4 can get SSH service through
TCP port 22.

List for declaring Slices in the Controller Application is given below:

```
# Slices 300 and 400 with their respective MAC addresses for ICMP
slices_data2 = [(300,"00:00:00:00:00:11","00:00:00:00:00:15","00:00:00:00:00:16",),
               (400,"00:00:00:00:00:14","00:00:00:00:00:12","00:00:00:00:00:13",) ]
# Slices 600 and 700 with their respective MAC addresses and TCP port
slices_data4 = [(600,"00:00:00:00:00:11","00:00:00:00:00:12","00:00:00:00:00:13",80),
               (700,"00:00:00:00:00:14","00:00:00:00:00:15","00:00:00:00:00:13",22)]
```

For the Implementation of the network check the documentation: [Project Documentation](https://github.com/sudo-riyad/OpenVirteX-Hypevisor-In-CORE/blob/15c2e701b4ad0e018ba997ec266048fbff0fecdd/Documentation/IndividualProject_Islam_Riyad-Ul-_1324662.pdf)
