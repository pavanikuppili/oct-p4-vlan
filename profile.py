"""OCT Alveo U280 profile with post-boot script for P4 experiments
"""

# Import the Portal object.
import geni.portal as portal
# Import the ProtoGENI library.
"""P4 nodes 
"""

# Import the Portal object.
import geni.portal as portal
# Import the ProtoGENI library.
import geni.rspec.pg as pg
# We use the URN library below.
import geni.urn as urn
# Emulab extension
import geni.rspec.emulab
#from ipaddress import IPv4Network, IPv6Network


# NODE_MIN=1
# NODE_MAX=4
# VLAN_MIN=3110
# VLAN_MAX=3119

# Create a portal context.
pc = portal.Context()

# Create a Request object to start building the RSpec.
request = pc.makeRequestRSpec()

# Pick your image.
imageList = [
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD', 'UBUNTU 20.04')    
    #('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU18-64-STD', 'UBUNTU 18.04'), 
    #('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU16-64-STD', 'UBUNTU 16.04'),
    #('urn:publicid:IDN+emulab.net+image+emulab-ops//CENTOS8-64-STD', 'CENTOS 8.4'),
    #('urn:publicid:IDN+emulab.net+image+emulab-ops//CENTOS7-64-STD', 'CENTOS 7.9')
] 

toolVersion = [('2023.1'),
               ('Do not install tools')]      

pc.defineParameter("nodes","List of nodes",
                   portal.ParameterType.STRING,"",
                   longDescription="Comma-separated list of nodes (e.g., pc164,pc165). Please check the list of available nodes within the Mass cluster at https://www.cloudlab.us/cluster-status.php before you specify the nodes.")

pc.defineParameter("toolVersion", "Tool Version",
                   portal.ParameterType.STRING,
                   toolVersion[0], toolVersion,
                   longDescription="Select a tool version. It is recommended to use the latest version for the deployment workflow. For more information, visit https://www.xilinx.com/products/boards-and-kits/alveo/u280.html#gettingStarted")   
pc.defineParameter("osImage", "Select Image",
                   portal.ParameterType.IMAGE,
                   imageList[0], imageList,
                   longDescription="Supported operating systems are Ubuntu and CentOS.")                    
# Optional ephemeral blockstore
pc.defineParameter("tempFileSystemSize", "Temporary Filesystem Size",
                   portal.ParameterType.INTEGER, 0,advanced=True,
                   longDescription="The size in GB of a temporary file system to mount on each of your " +
                   "nodes. Temporary means that they are deleted when your experiment is terminated. " +
                   "The images provided by the system have small root partitions, so use this option " +
                   "if you expect you will need more space to build your software packages or store " +
                   "temporary files.")
# Instead of a size, ask for all available space. 
pc.defineParameter("tempFileSystemMax",  "Temp Filesystem Max Space",
                    portal.ParameterType.BOOLEAN, False,
                    advanced=True,
                    longDescription="Instead of specifying a size for your temporary filesystem, " +
                    "check this box to allocate all available disk space. Leave the size above as zero.")

pc.defineParameter("tempFileSystemMount", "Temporary Filesystem Mount Point",
                   portal.ParameterType.STRING,"/mydata",advanced=True,
                   longDescription="Mount the temporary file system at this mount point; in general you " +
                   "you do not need to change this, but we provide the option just in case your software " +
                   "is finicky.")  


#pc.defineParameter("vlan", "VLAN ID", portal.ParameterType.INTEGER, 3111)
# Retrieve the values the user specifies during instantiation.

params = pc.bindParameters()     

# parameterize the vlan to use

#portal.context.defineParameter("ip_subnet", "IP_SUBNET", portal.ParameterType.STRING, "192.168.1.0/24")
#portal.context.defineParameter("node_count", "NODE_COUNT", portal.ParameterType.INTEGER, NODE_MIN)
#params = portal.context.bindParameters()

# Check parameter validity.
  
pc.verifyParameters()

lan1 = request.Link("link1", "vlan")
lan2 = request.Link("link2", "vlan")

lan1.setVlanTag(2711)
lan2.setVlanTag(2712)

nodeList = params.nodes.split(',')
i = 0
for nodeName in nodeList:
    host = request.RawPC(nodeName)
    # UMass cluster
    host.component_manager_id = "urn:publicid:IDN+cloudlab.umass.edu+authority+cm"
    # Assign to the node hosting the FPGA.
    host.component_id = nodeName
    host.disk_image = params.osImage
    
    # Optional Blockstore
    if params.tempFileSystemSize > 0 or params.tempFileSystemMax:
        bs = host.Blockstore(nodeName + "-bs", params.tempFileSystemMount)
        if params.tempFileSystemMax:
            bs.size = "0GB"
        else:
            bs.size = str(params.tempFileSystemSize) + "GB"
        bs.placement = "any"

    if params.toolVersion != "Do not install tools":
        host.addService(pg.Execute(shell="bash", command="sudo /local/repository/post-boot.sh " + params.toolVersion + " >> /local/repository/output_log.txt"))

    # Since we want to create network links to the FPGA, it has its own identity.
    fpga = request.RawPC("fpga-" + nodeName)
    # UMass cluster
    fpga.component_manager_id = "urn:publicid:IDN+cloudlab.umass.edu+authority+cm"
    # Assign to the fgpa node
    fpga.component_id = "fpga-" + nodeName
    # Use the default image for the type of the node selected. 
    fpga.setUseTypeDefaultImage()

    # Secret sauce.
    fpga.SubNodeOf(host)
    

    
    
    # lan2.setVlanTag(3112)
    if i==0:
        host_iface1 = host.addInterface()
        host_iface1.component_id = "eth2"
        host_iface1.addAddress(pg.IPv4Address("192.168.40." + str(i+30), "255.255.255.0")) 
        fpga_iface1 = fpga.addInterface()
        fpga_iface1.component_id = "eth0"
        fpga_iface1.addAddress(pg.IPv4Address("192.168.50." + str(i+10), "255.255.255.0"))
        fpga_iface2 = fpga.addInterface()
        fpga_iface2.component_id = "eth1"
        fpga_iface2.addAddress(pg.IPv4Address("192.168.50." + str(i+20), "255.255.255.0"))
        lan2.addInterface(fpga_iface1)
        lan2.addInterface(fpga_iface2)
        lan1.addInterface(host_iface1)
    if i==1:
        host_iface1 = host.addInterface()
        host_iface1.component_id = "eth2"
        host_iface1.addAddress(pg.IPv4Address("192.168.50." + str(i+30), "255.255.255.0"))
        lan2.addInterface(host_iface1)
        

    lan1.link_multiplexing = True;
    lan1.best_effort = True;

   # lan2.link_multiplexing = True;
   # lan2.best_effort = True;
  
    i+=1

# Print Request RSpec
pc.printRequestRSpec(request)
