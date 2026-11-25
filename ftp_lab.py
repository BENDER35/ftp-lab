#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ftp_lab.py - Cliente FTP interactivo para laboratorios de ciberseguridad.

Herramienta didactica y multiplataforma (Windows / Linux / macOS) escrita
unicamente con la biblioteca estandar de Python. Permite conectarse a un
servidor FTP propio o autorizado, explorar directorios, subir/descargar
archivos y practicar con FTP, FTPS, modo activo/pasivo y registro de sesion.

USO AUTORIZADO UNICAMENTE: usa este programa solo contra equipos propios o
aquellos para los que tengas permiso explicito. El protocolo FTP transmite
credenciales en texto plano; no lo uses en redes o servidores que no sean
de tu laboratorio.
"""

from __future__ import annotations

import argparse
import cmd
import configparser
import ftplib
import getpass
import logging
import os
import ssl
import sys
from pathlib import Path
from typing import Optional

__version__ = "1.0.0"

LOG = logging.getLogger("ftp_lab")


def configure_logging(logfile: Optional[str], debug: bool) -> None:
    """Configura la salida por consola y, si se pide, un fichero de sesion."""
    level = logging.DEBUG if debug else logging.INFO
    LOG.setLevel(level)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%Y-%m-%d %H:%M:%S")

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(fmt)
    LOG.addHandler(stream)

    if logfile:
        path = Path(logfile).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(path, encoding="utf-8")
        handler.setFormatter(fmt)
        LOG.addHandler(handler)
        LOG.info("Registro de sesion: %s", path)


def human_size(num_bytes: int) -> str:
    """Devuelve un tamano legible para humanos."""
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{value:.1f} TB"


class FTPShell(cmd.Cmd):
    """Intérprete de comandos FTP (similar al cliente 'ftp' clasico)."""

    intro = (
        "ftp-lab v" + __version__ + " | Escribe 'help' para ver los comandos, 'quit' para salir.\n"
        "Recuerda: usa este cliente solo en equipos propios o autorizados."
    )
    prompt = "ftp> "

    def __init__(self, ftp, timeout: int = 30):
        super().__init__()
        self.ftp = ftp
        self.timeout = timeout
        self._update_prompt()

    # ------------------------------------------------------------------ utils
    def _update_prompt(self) -> None:
        try:
            self.prompt = f"ftp:{self.ftp.pwd()}> "
        except Exception:
            self.prompt = "ftp> "

    def _transfer_callback(self, chunk: bytes) -> None:
        sys.stdout.write(".")
        sys.stdout.flush()

    def _finish_transfer(self, count: int) -> None:
        print(f"\nTransferencia completada: {count} bytes ({human_size(count)}).")

    def onecmd(self, line: str):
        """Envoltorio comun de errores para todos los comandos."""
        try:
            return super().onecmd(line)
        except ftplib.all_errors + (ValueError,) as exc:
            LOG.error("Error: %s", exc)
            return False

    def emptyline(self) -> bool:
        return False

    def default(self, line: str) -> None:
        print(f"Comando desconocido: {line!r}. Escribe 'help'.")

    # --------------------------------------------------------------- comandos
    def do_pwd(self, _arg: str) -> None:
        """Muestra el directorio actual en el servidor."""
        print(self.ftp.pwd())

    def do_ls(self, arg: str) -> None:
        """Lista el directorio remoto. Uso: ls [ruta]"""
        arg = arg.strip()
        command = f"LIST {arg}" if arg else "LIST"
        self.ftp.retrlines(command, print)

    def do_dir(self, arg: str) -> None:
        """Alias de 'ls' con el formato LIST del servidor. Uso: dir [ruta]"""
        self.do_ls(arg)

    def do_cd(self, arg: str) -> None:
        """Cambia de directorio remoto. Uso: cd <ruta>"""
        if not arg.strip():
            print("Uso: cd <ruta>")
            return
        self.ftp.cwd(arg.strip())
        self._update_prompt()
        print(f"Directorio actual: {self.ftp.pwd()}")

    def do_get(self, arg: str) -> None:
        """Descarga un archivo remoto. Uso: get <remoto> [local]"""
        parts = arg.split()
        if not parts:
            print("Uso: get <archivo_remoto> [archivo_local]")
            return
        remote = parts[0]
        local = parts[1] if len(parts) > 1 else os.path.basename(remote.replace("\\", "/"))
        counter = {"n": 0}

        LOG.info("Descargando %s -> %s", remote, local)
        with open(local, "wb") as handle:
            def callback(chunk: bytes) -> None:
                handle.write(chunk)
                counter["n"] += len(chunk)
                self._transfer_callback(chunk)

            self.ftp.retrbinary(f"RETR {remote}", callback)
        self._finish_transfer(counter["n"])

    def do_put(self, arg: str) -> None:
        """Sube un archivo local. Uso: put <local> [remoto]"""
        parts = arg.split()
        if not parts:
            print("Uso: put <archivo_local> [archivo_remoto]")
            return
        local = parts[0]
        remote = parts[1] if len(parts) > 1 else os.path.basename(local)
        counter = {"n": 0}

        def callback(chunk: bytes) -> None:
            counter["n"] += len(chunk)
            self._transfer_callback(chunk)

        LOG.info("Subiendo %s -> %s", local, remote)
        with open(local, "rb") as handle:
            self.ftp.storbinary(f"STOR {remote}", handle, callback=callback)
        self._finish_transfer(counter["n"])

    def do_mkdir(self, arg: str) -> None:
        """Crea un directorio remoto. Uso: mkdir <nombre>"""
        if not arg.strip():
            print("Uso: mkdir <nombre>")
            return
        print(self.ftp.mkd(arg.strip()))

    def do_rmdir(self, arg: str) -> None:
        """Borra un directorio remoto (debe estar vacio). Uso: rmdir <nombre>"""
        if not arg.strip():
            print("Uso: rmdir <nombre>")
            return
        self.ftp.rmd(arg.strip())
        print("Directorio eliminado.")

    def do_delete(self, arg: str) -> None:
        """Borra un archivo remoto. Uso: delete <archivo>"""
        if not arg.strip():
            print("Uso: delete <archivo>")
            return
        self.ftp.delete(arg.strip())
        print("Archivo eliminado.")

    def do_rename(self, arg: str) -> None:
        """Renombra un archivo remoto. Uso: rename <viejo> <nuevo>"""
        parts = arg.split()
        if len(parts) != 2:
            print("Uso: rename <nombre_viejo> <nombre_nuevo>")
            return
        self.ftp.rename(parts[0], parts[1])
        print("Archivo renombrado.")

    def do_size(self, arg: str) -> None:
        """Muestra el tamano de un archivo remoto. Uso: size <archivo>"""
        if not arg.strip():
            print("Uso: size <archivo>")
            return
        print(human_size(int(self.ftp.size(arg.strip()))))

    def do_binary(self, _arg: str) -> None:
        """Activa el modo de transferencia binario (recomendado)."""
        self.ftp.voidcmd("TYPE I")
        print("Modo binario activado.")

    def do_ascii(self, _arg: str) -> None:
        """Activa el modo de transferencia ASCII (solo texto)."""
        self.ftp.voidcmd("TYPE A")
        print("Modo ASCII activado.")

    def do_passive(self, _arg: str) -> None:
        """Activa el modo pasivo (recomendado tras NAT/firewall)."""
        self.ftp.set_pasv(True)
        print("Modo pasivo activado (PASV).")

    def do_active(self, _arg: str) -> None:
        """Activa el modo activo (necesita abrir puerto entrante)."""
        self.ftp.set_pasv(False)
        print("Modo activo activado (PORT). Atencion: puede requerir reglas de firewall.")

    def do_status(self, _arg: str) -> None:
        """Muestra informacion de la sesion actual."""
        secure = isinstance(self.ftp, ftplib.FTP_TLS)
        print(f"Servidor      : {getattr(self.ftp, 'host', 'desconocido')}")
        print(f"Directorio    : {self.ftp.pwd()}")
        print(f"Modo pasivo   : {self.ftp.passiveserver if hasattr(self.ftp, 'passiveserver') else 'n/d'}")
        print(f"TLS/FTPS      : {'si' if secure else 'no'}")
        print(f"Timeout       : {self.timeout}s")

    def do_debug(self, arg: str) -> None:
        """Fija el nivel de depuracion del protocolo (0-3). Uso: debug <n>"""
        try:
            self.ftp.set_debuglevel(int(arg.strip() or 0))
        except ValueError:
            print("Uso: debug <0|1|2|3>")

    def do_quit(self, _arg: str) -> bool:
        """Cierra la sesion y sale del programa."""
        print("Cerrando sesion...")
        return True

    def do_exit(self, arg: str) -> bool:
        """Alias de 'quit'."""
        return self.do_quit(arg)

    def do_bye(self, arg: str) -> bool:
        """Alias de 'quit'."""
        return self.do_quit(arg)


def load_profile(path: Path, name: str) -> dict:
    """Lee un perfil guardado en un fichero INI."""
    parser = configparser.ConfigParser()
    if not path.exists():
        raise FileNotFoundError(f"No existe el fichero de perfiles: {path}")
    parser.read(path, encoding="utf-8")
    if name not in parser:
        raise KeyError(f"Perfil {name!r} no encontrado. Perfiles: {', '.join(parser.sections())}")
    data = dict(parser[name])
    data["port"] = int(data.get("port", 21))
    data["secure"] = data.get("secure", "false").lower() in ("1", "true", "yes", "on")
    data["no_verify_ssl"] = data.get("no_verify_ssl", "false").lower() in ("1", "true", "yes", "on")
    return data


def build_connection(args: argparse.Namespace) -> ftplib.FTP:
    """Crea y autentica la conexion FTP/FTPS."""
    host = args.host
    port = args.port
    timeout = args.timeout

    if args.secure:
        context = ssl._create_unverified_context() if args.no_verify_ssl else ssl.create_default_context()
        ftp: ftplib.FTP = ftplib.FTP_TLS(context=context)
    else:
        ftp = ftplib.FTP()

    ftp.set_debuglevel(args.debug)
    ftp.set_pasv(not args.active)
    ftp.connect(host, port, timeout=timeout)

    password = args.password if args.password is not None else getpass.getpass("Contrasena: ")
    ftp.login(args.user, password)
    if args.secure:
        # Protege tambien el canal de datos; sin esto solo el control va cifrado.
        ftp.prot_p()
    LOG.info("Conectado a %s:%s como %s%s", host, port, args.user, " (FTPS)" if args.secure else "")
    if not args.secure:
        LOG.warning("FTP sin cifrar: usuario y contrasena viajan en texto plano.")
    return ftp


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cliente FTP interactivo para practicar ciberseguridad en un laboratorio local.",
        epilog=(
            "Ejemplo: python ftp_lab.py --host 127.0.0.1 --port 2121 --user labuser "
            "--password labpass --log sesion.log\n"
            "Perfil:  python ftp_lab.py --profile laboratorio\n"
            "Uso autorizado unicamente contra equipos propios o con permiso explicito."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--host", help="IP o nombre del servidor FTP")
    parser.add_argument("--port", type=int, default=21, help="Puerto FTP (por defecto: 21)")
    parser.add_argument("--user", default="anonymous", help="Usuario (por defecto: anonymous)")
    parser.add_argument("--password", help="Contrasena; si se omite se pide de forma segura")
    parser.add_argument("--profile", help="Nombre de perfil en ./profiles.ini")
    parser.add_argument("--profiles-file", default="profiles.ini", help="Fichero INI de perfiles")
    parser.add_argument("--secure", action="store_true", help="Usar FTPS (FTP sobre TLS)")
    parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="No verificar el certificado TLS (solo para certificados auto-firmados del laboratorio)",
    )
    parser.add_argument("--active", action="store_true", help="Usar modo activo en vez del pasivo")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout en segundos (por defecto: 30)")
    parser.add_argument("--debug", type=int, choices=range(0, 4), default=0, help="Nivel de debug 0-3")
    parser.add_argument("--log", help="Guardar la sesion en un fichero de texto")
    parser.add_argument(
        "--command",
        action="append",
        default=[],
        help="Ejecutar un comando y salir (se puede repetir). Ej: --command pwd --command 'ls'",
    )
    parser.add_argument("--version", action="version", version=f"ftp_lab {__version__}")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    configure_logging(args.log, args.debug > 0)

    if args.profile:
        try:
            profile = load_profile(Path(args.profiles_file).expanduser().resolve(), args.profile)
        except (FileNotFoundError, KeyError, ValueError) as exc:
            LOG.error("No se pudo cargar el perfil: %s", exc)
            return 2
        # Los valores pasados explicitamente en la linea de comandos ganan al perfil.
        explicit = {
            token.lstrip("-").split("=", 1)[0]
            for token in (argv if argv is not None else sys.argv[1:])
            if token.startswith("--")
        }
        for key, value in profile.items():
            if hasattr(args, key) and key.replace("_", "-") not in explicit:
                setattr(args, key, value)

    if not args.host:
        LOG.error("Falta --host (o un perfil que lo defina). Usa --help.")
        return 2

    try:
        ftp = build_connection(args)
    except ftplib.all_errors + (ssl.SSLError,) as exc:
        LOG.error("No se pudo conectar: %s", exc)
        return 1

    shell = FTPShell(ftp, timeout=args.timeout)
    try:
        if args.command:
            for command in args.command:
                LOG.info("> %s", command)
                shell.onecmd(command)
        else:
            shell.cmdloop()
    except KeyboardInterrupt:
        print("\nSesion interrumpida por el usuario.")
    finally:
        try:
            ftp.quit()
        except ftplib.all_errors:
            ftp.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
