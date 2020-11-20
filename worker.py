from threading import Timer
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import xml.etree.ElementTree as ET
import xmlrpc.client


# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)


network = ET.parse('network.xml')
root = network.getroot()

port = -1
connections = []


def is_port_in_use(p_port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        connected = s.connect_ex(('localhost', p_port)) == 0
        s.close()
    return connected


def connect_to_neighbors():
    for neighbor in root.iter('neighbor'):
        check = is_port_in_use(int(neighbor.attrib['port']))
        curr_port = neighbor.attrib['port']
        if curr_port == port or not check:
            continue
        s = xmlrpc.client.ServerProxy('http://localhost:' + curr_port)
        connections.append(s)


for neighbor in root.iter('neighbor'):
    check = is_port_in_use(int(neighbor.attrib['port']))
    print(check)
    if not check:
        port = int(neighbor.attrib['port'])
        if port == 8000:
            connect_to_neighbors()
        break


print(port)
# Create server
with SimpleXMLRPCServer(('localhost', port),
                        requestHandler=RequestHandler) as server:
    server.register_introspection_functions()

    class WorkerFunctions:
        store = {}

        def set_value(self, name, value):
            print('setting ' + value + ' to ' + name)
            self.store[name] = value
            for con in connections:
                con.set_value(name,value)
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

        def expire(self, name, time):
            print("Will expire " + name + "after " + time + "second(s)")
            for con in connections:
                con.expire(name,time)
            Timer(float(time), self.delete, name).start()
            return "200"


    server.register_instance(WorkerFunctions())

    # Run the server's main loop
    server.serve_forever()
