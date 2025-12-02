from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

def on_param(address, *args):
    print(f"[PARAM] {address} -> {args}")

def on_meta(address, *args):
    print(f"[META]  {address} -> {args}")

def main():
    disp = Dispatcher()
    disp.map("/param/*", on_param)
    disp.map("/meta/*",  on_meta)

    ip = "127.0.0.1"
    port = 9000  
    print(f"Listening on {ip}:{port} ...")
    server = BlockingOSCUDPServer((ip, port), disp)
    server.serve_forever()

if __name__ == "__main__":
    main()
