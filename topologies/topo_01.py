from mininet.topo import Topo 
from mininet.link import TCLink

class MyTopo( Topo ):  
    "Simple topology example."
    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        Host1 = self.addHost( 'h1')
        Host2 = self.addHost( 'h2')
        Host3 = self.addHost('h3')
        Switch1 = self.addSwitch('s1')

        # Add links
        self.addLink( Host1, Switch1, cls=TCLink, bw=50, delay='0ms', loss=0, max_queue_size=1024, use_htb=True )
        self.addLink( Host2, Switch1, cls=TCLink, bw=50, delay='0ms', loss=0, max_queue_size=1024, use_htb=True )
        self.addLink( Host3, Switch1, cls=TCLink, bw=50, delay='0ms', loss=0, max_queue_size=1024, use_htb=True )
       

topos = { 'mytopo': ( lambda: MyTopo() ) } 