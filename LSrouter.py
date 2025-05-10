####################################################
# LSrouter.py
# Name:
# HUID:
#####################################################

from router import Router
import heapq
from packet import Packet
import time
import json


class LSrouter(Router):
    """Link state routing protocol implementation.

    Add your own class fields and initialization code (e.g. to create forwarding table
    data structures). See the `Router` base class for docstrings of the methods to
    override.
    """

    def __init__(self, addr, heartbeat_time):
        Router.__init__(self, addr)
        self.heartbeat_time = heartbeat_time
        self.last_time = 0
        self.seq_num = 0
        self.neighbors = {}  # {port: (neighbor, cost)}
        self.link_state_db = {}  # {router_addr: (seq_num, [(neighbor, cost), ...])}
        self.forwarding_table = {}  # {dest: port}


    def handle_packet(self, port, packet):
        if packet.is_traceroute:
            dst = packet.dst_addr
            if dst in self.forwarding_table:
                self.send(self.forwarding_table[dst], packet)
        elif packet.is_routing:
            try:
                origin, seq, nbrs = json.loads(packet.content)
            except (ValueError, TypeError):
                return

            stored = self.link_state_db.get(origin)
            if stored is None or seq > stored[0]:
                self.link_state_db[origin] = (seq, nbrs)
                self.recompute_paths()
                for p, (nbr, _) in self.neighbors.items():
                    if p != port:
                        pkt = Packet(Packet.ROUTING, origin, nbr, packet.content)
                        self.send(p, pkt)

    def handle_new_link(self, port, endpoint, cost):
        self.neighbors[port] = (endpoint, cost)
        self.seq_num += 1
        self.link_state_db[self.addr] = (
            self.seq_num,
            [(ep, c) for _, (ep, c) in self.neighbors.items()]
        )
        print(f"[DEBUG] {self.addr} thêm link tới {endpoint} với cost {cost}")
        self.flood()
        self.recompute_paths()

    def handle_remove_link(self, port):
        if port in self.neighbors:
            del self.neighbors[port]
            self.seq_num += 1
            self.link_state_db[self.addr] = (
                self.seq_num,
                [(ep, c) for _, (ep, c) in self.neighbors.items()]
            )
            print(f"[DEBUG] {self.addr} xóa link trên port {port}")
            self.flood()
            self.recompute_paths()

    def handle_time(self, time_ms):
        if time_ms - self.last_time >= self.heartbeat_time:
            self.last_time = time_ms
            self.flood()

    def recompute_paths(self):
        print(f"[DEBUG] recompute_paths() được gọi bởi router {self.addr}")
        graph = {}
        for router, (_, links) in self.link_state_db.items():
            graph[router] = {neighbor: cost for neighbor, cost in links}

        dist = {self.addr: 0}
        prev = {}
        visited = set()
        heap = [(0, self.addr)]

        while heap:
            cost, node = heapq.heappop(heap)
            if node in visited:
                continue
            visited.add(node)

            for neighbor, weight in graph.get(node, {}).items():
                new_cost = cost + weight
                if neighbor not in dist or new_cost < dist[neighbor]:
                    dist[neighbor] = new_cost
                    prev[neighbor] = node
                    heapq.heappush(heap, (new_cost, neighbor))

        self.forwarding_table.clear()
        for dest in dist:
            if dest == self.addr:
                continue
            # Truy vết đường đi để tìm next hop
            next_hop = dest
            while prev[next_hop] != self.addr:
                next_hop = prev[next_hop]
            for p, (ep, _) in self.neighbors.items():
                if ep == next_hop:
                    self.forwarding_table[dest] = p
                    break

    def flood(self):
            print(f"[DEBUG] {self.addr} flooding LSP seq={self.seq_num}")
            content = json.dumps([
                self.addr,
                self.seq_num,
                [(ep, c) for _, (ep, c) in self.neighbors.items()]
            ])
            for port in self.neighbors:
                pkt = Packet(Packet.ROUTING, self.addr, 'ALL', content)
                self.send(port, pkt)


    def __repr__(self):
        """Representation for debugging in the network visualizer."""
        return f"LSrouter(addr={self.addr}, neighbors={list(self.neighbors.values())})"
