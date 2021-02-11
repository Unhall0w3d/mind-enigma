import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

while True:
    try:
        s.connect(('10.16.10.140', 3804))
        print(" Port 3804 is reachable ")
        break
        exit()
    except socket.error as e:
        print(" Port 3804 is not up ")
        exit()
