import threading
import time
from models import db, Server
from ssh_utils import ssh_connect, get_status

class StatusUpdater(threading.Thread):
    def __init__(self, app, interval=30):
        super().__init__()
        self.app = app
        self.interval = interval
        self.daemon = True
        self.running = True

    def run(self):
        with self.app.app_context():
            while self.running:
                try:
                    servers = Server.query.all()
                    for server in servers:
                        try:
                            client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
                            status = get_status(client, server.name)
                            if server.status != status:
                                server.status = status
                            client.close()
                        except Exception:
                            if server.status != 'offline':
                                server.status = 'offline'
                    db.session.commit()
                except Exception as e:
                    print(f"Status updater error: {e}")
                time.sleep(self.interval)

    def stop(self):
        self.running = False