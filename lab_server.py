#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lab_server.py - Servidor FTP local para practicar con ftp_lab.py.

Necesita el paquete opcional 'pyftpdlib':
    python -m pip install -r requirements-dev.txt

Por defecto escucha SOLO en 127.0.0.1 (loopback), por lo que no es accesible
desde otras maquinas. Para practicar en tu red local usa --allow-lan de forma
conscienzuda y con un usuario/contrasena propios. No lo expongas a Internet.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from pyftpdlib.authorizers import DummyAuthorizer
    from pyftpdlib.handlers import FTPHandler
    from pyftpdlib.servers import FTPServer
except ImportError as exc:
    sys.exit(f"Falta pyftpdlib ({exc}). Instalalo con: python -m pip install -r requirements-dev.txt")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Servidor FTP didactico para laboratorio local.")
    parser.add_argument("--host", default="127.0.0.1", help="Direccion de escucha (por defecto: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=2121, help="Puerto de escucha (por defecto: 2121)")
    parser.add_argument("--root", default="./ftp_root", help="Directorio raiz servido")
    parser.add_argument("--user", default="labuser", help="Usuario FTP")
    parser.add_argument("--password", default="labpass", help="Contrasena FTP (cambiala en tu laboratorio)")
    parser.add_argument("--allow-lan", action="store_true", help="Permitir escuchar en 0.0.0.0 (red local)")
    parser.add_argument("--allow-write", action="store_true", help="Permitir subir/borrar archivos")
    parser.add_argument("--anonymous", action="store_true", help="Permitir acceso anonimo de solo lectura")
    parser.add_argument("--tls", action="store_true", help="Habilitar FTPS con certificado propio")
    parser.add_argument("--cert", default="./cert.pem", help="Certificado TLS (con --tls)")
    parser.add_argument("--key", default="./key.pem", help="Clave privada TLS (con --tls)")
    args = parser.parse_args()

    if args.host != "127.0.0.1" and not args.allow_lan:
        parser.error("Para escuchar fuera de loopback necesitas --allow-lan (usa solo en tu red local).")
    if args.allow_lan:
        args.host = "0.0.0.0"
        print("AVISO: servidor accesible desde tu red local. No lo expongas a Internet.")
    return args


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    sample = root / "README.txt"
    if not sample.exists():
        sample.write_text(
            "Servidor FTP de laboratorio.\n"
            "Este archivo se creo automaticamente para la practica.\n",
            encoding="utf-8",
        )

    authorizer = DummyAuthorizer()
    # e=cambiar dir, l=listar, r=leer, a=append, d=borrar, f=renombrar,
    # m=mkdir, w=escribir.
    perm = "elradfmw" if args.allow_write else "elr"
    authorizer.add_user(args.user, args.password, str(root), perm=perm)
    if args.anonymous:
        authorizer.add_anonymous(str(root), perm="lr")

    if args.tls:
        try:
            from pyftpdlib.handlers import TLS_FTPHandler
        except ImportError:
            print("FTPS necesita pyOpenSSL: python -m pip install pyOpenSSL")
            return 2
        if not Path(args.cert).exists() or not Path(args.key).exists():
            print("Genera el certificado con: openssl req -x509 -newkey rsa:2048 -nodes "
                  "-keyout key.pem -out cert.pem -days 30 -subj '/CN=localhost'")
            return 2
        handler = TLS_FTPHandler
        handler.certfile = args.cert
        handler.keyfile = args.key
        handler.tls_control_required = True
        handler.tls_data_required = True
        print("FTPS activado: el cliente debe usar --secure --no-verify-ssl.")
    else:
        handler = FTPHandler
        print("AVISO: FTP sin cifrar. Usuario y contrasena viajan en texto plano.")

    handler.authorizer = authorizer
    handler.banner = "Laboratorio FTP didactico (solo uso autorizado)"
    server = FTPServer((args.host, args.port), handler)
    print(f"Sirviendo {root} en ftp://{args.host}:{args.port}/  (Ctrl+C para detener)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        server.close_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
