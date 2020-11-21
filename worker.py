from threading import Timer
from threading import Thread
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import xml.etree.ElementTree as ET
import xmlrpc.client
import time


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)


network = ET.parse('network.xml')
root = network.getroot()

port = -1
connections = []
master_port = 8000


def find_instance_time(p):
    net = root.findall('neighbor')
    for n in net:
        print(n.find('wait_time'))


def is_port_in_use(p_port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        connected = s.connect_ex(('localhost', p_port)) == 0
        s.close()
    return connected


def init_connection():
    global port
    for neighbor in root.iter('neighbor'):
        check = is_port_in_use(int(neighbor.attrib['port']))
        if not check:
            port = int(neighbor.attrib['port'])
            break


init_connection()


def connect_to_neighbors():
    if port != master_port:
        return
    global connections
    temp = []
    for neighbor in root.iter('neighbor'):
        curr_port = int(neighbor.attrib['port'])
        check = is_port_in_use(curr_port)
        if curr_port != master_port and check:
            s = xmlrpc.client.ServerProxy('http://localhost:' + str(curr_port))
            temp.append(s)
    connections = temp
    if port == master_port:
        Timer(5.0, connect_to_neighbors).start()


if port == master_port:
    connect_to_neighbors()


server = SimpleXMLRPCServer(('localhost', port),requestHandler=RequestHandler)
server.register_introspection_functions()


class WorkerFunctions:
    store = {}

    def set_value(self, name, value):
        print('setting ' + value + ' to ' + name)
        self.store[name] = value
        for con in connections:
            con.set_value(name, value)
        return "200"

    def get_value(self, name):
        return self.store[name] if name in self.store else 'No encontrado'

    def inc(self, name):
        print('Incrementing ' + name)
        for con in connections:
            con.inc(name)
        if name in self.store and self.store[name].isnumeric():
            num = int(self.store[name])
            num += 1
            self.store[name] = str(num)
            return "200"
        return "400"

    def delete(self, name):
        print("Deleting " + name)
        for con in connections:
            con.delete(name)
        return self.store.pop(name, 'None')

    def expire(self, name, t):
        print("Will expire " + name + "after " + t + "second(s)")
        for con in connections:
            con.expire(name, t)
        Timer(float(t), self.delete, name).start()
        return "200"


server.register_instance(WorkerFunctions())


def start_server(ser):
    global server
    server.serve_forever()
    # Run the server's main loop


Thread(target=start_server, args=('',)).start()
print(port)


def master_health_check():
    global server
    global port
    if not is_port_in_use(master_port):
        print('Connecting master port..')
        server.shutdown()
        port = master_port
        server = SimpleXMLRPCServer(('localhost', port), requestHandler=RequestHandler)
        server.register_instance(WorkerFunctions())
        connect_to_neighbors()
        Thread(target=start_server, args=('',)).start()
    Timer(2.0, master_health_check).start()


if port != master_port:
    master_health_check()
