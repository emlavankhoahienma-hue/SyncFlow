import socket
import logging
from typing import Optional

logger = logging.getLogger("syncflow.discovery")

class BonjourServer:
    def __init__(self, port: int = 8765):
        self.port = port
        self.zeroconf = None
        self.service_info = None

    def start(self):
        try:
            from zeroconf import Zeroconf, ServiceInfo

            hostname = socket.gethostname()
            local_ip = self.get_local_ip()

            desc = {"version": "1.0.0", "path": "/health"}
            self.service_info = ServiceInfo(
                "_syncflow._tcp.local.",
                f"{hostname}._syncflow._tcp.local.",
                addresses=[socket.inet_aton(local_ip)],
                port=self.port,
                properties=desc,
                server=f"{hostname}.local.",
            )

            self.zeroconf = Zeroconf()
            self.zeroconf.register_service(self.service_info)
            logger.info(f"Bonjour service registered: {hostname}._syncflow._tcp.local. on {local_ip}:{self.port}")
        except Exception as e:
            logger.warning(f"Could not start Zeroconf mDNS advertiser: {e}")

    def stop(self):
        try:
            if self.zeroconf and self.service_info:
                self.zeroconf.unregister_service(self.service_info)
                self.zeroconf.close()
                logger.info("Bonjour service stopped")
        except Exception as e:
            logger.warning(f"Error stopping Zeroconf: {e}")

    @staticmethod
    def get_local_ip() -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip
