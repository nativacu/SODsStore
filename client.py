import xmlrpc.client

s = xmlrpc.client.ServerProxy('http://localhost:8000')
while True:
    print('Comandos: [set, get, inc, expire, delete]')
    print('Inserte el comando a ejecutar:')
    funcInput = input().lower()
    if funcInput == 'set':
        print('Nombre a insertar:')
        name = input()
        print('Valor de ' + name + ':')
        value = input()
        s.set_value(name, value)
    elif funcInput == 'get':
        print('Nombre del valor a conseguir:')
        name = input()
        print(s.get_value(name))
    elif funcInput == 'inc':
        print('Nombre del valor a incrementar:')
        name = input()
        s.inc(name)
    elif funcInput == 'expire':
        print('Nombre del valor a expirar:')
        name = input()
        print('Segundos en los que expira ' + name + ':')
        time = input()
        s.expire(name, time)
    elif funcInput == 'delete':
        print('Nombre del valor a borrar:')
        name = input()
        s.delete(name)
    else:
        continue
