from pythonosc.udp_client import SimpleUDPClient
import time, math

# IP/port
client = SimpleUDPClient("127.0.0.1", 9000)

def main():
    t0 = time.time()
    while True:
        t = time.time() - t0
        # Paradeigma Parametrwn
        cutoff = max(200.0, min(8000.0, 2000.0 + 1000.0*math.sin(2*math.pi*0.25*t)))
        res    = 0.7 + 0.2*abs(math.sin(2*math.pi*0.15*t))
        fb     = 0.3 + 0.2*abs(math.sin(2*math.pi*0.10*t))
        wet    = 0.2 + 0.2*abs(math.sin(2*math.pi*0.07*t))

        client.send_message("/param/cutoff", float(cutoff))
        client.send_message("/param/res",    float(res))
        client.send_message("/param/delay/feedback", float(fb))
        client.send_message("/param/mix",    float(wet))

        # tick gia latency tests (token, timestamp)
        client.send_message("/meta/latencyTick", [int(t*1000) % 100000, float(time.time())])

        print(f"sent cutoff={cutoff:.1f} res={res:.2f} fb={fb:.2f} wet={wet:.2f}", end="\r")
        time.sleep(0.1)  # 10Hz demo

if __name__ == "__main__":
    main()
