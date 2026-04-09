from __future__ import annotations

import argparse
import sys

import uvicorn

from app.cli import run_cli, run_launcher


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Talk2Shell")
    parser.add_argument("--launcher", action="store_true", help="Open the terminal launcher menu")
    parser.add_argument("--terminal", action="store_true", help="Skip the launcher and go straight to terminal mode")
    parser.add_argument("--web", action="store_true", help="Start the FastAPI web server instead of the terminal UI")
    parser.add_argument("--native-window", action="store_true", help="Open Talk2Shell in a native terminal window on Windows")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args(argv)


def _maybe_open_native_window(args: argparse.Namespace) -> bool:
    if not args.native_window:
        return False
    if sys.platform != "win32":
        return False

    from app.cli import _run_in_native_terminal

    return _run_in_native_terminal(["--launcher"])


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    if _maybe_open_native_window(args):
        raise SystemExit(0)
    if args.web:
        uvicorn.run("app.main:app", host=args.host, port=args.port, reload=False)
    elif args.terminal:
        run_cli()
    elif args.launcher:
        run_launcher(host=args.host, port=args.port)
    else:
        run_launcher(host=args.host, port=args.port)
