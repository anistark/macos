import argparse
import os
import webbrowser

from use_computer import Computer, SandboxType

BASE_URL = os.environ.get("USE_COMPUTER_BASE_URL", "https://api.dev.use.computer")
API_KEY = os.environ["USE_COMPUTER_API_KEY"]


def novnc_url(sandbox_id: str) -> str:
    return f"{BASE_URL}/vnc?sandbox={sandbox_id}&token={API_KEY}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sandbox-id",
        help="Connect to an existing sandbox instead of creating a new one.",
    )
    args = parser.parse_args()

    client = Computer(api_key=API_KEY, base_url=BASE_URL)

    if args.sandbox_id:
        print(f"Connecting to existing sandbox {args.sandbox_id}...")
        mac = client.get(args.sandbox_id)
        created = False
    else:
        print("Booting macOS sandbox...")
        mac = client.create(type=SandboxType.MACOS)
        created = True

    url = novnc_url(mac.sandbox_id)
    print(f"sandbox_id : {mac.sandbox_id}")
    print(f"ssh_url    : {getattr(mac, 'ssh_url', '')}")
    print(f"vnc_url    : {url}")

    mac.start_keepalive()
    webbrowser.open(url)

    try:
        input("\nVNC opened in browser. Press Enter to exit"
              + (" and shut down the sandbox..." if created else "..."))
    finally:
        mac.stop_keepalive()
        if created:
            print("Closing sandbox...")
            mac.close()
        client.close()


if __name__ == "__main__":
    main()
