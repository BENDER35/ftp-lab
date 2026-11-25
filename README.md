# ftp-lab

[![Mirror a GitLab](https://github.com/BENDER35/ftp-lab/actions/workflows/mirror.yml/badge.svg)](https://github.com/BENDER35/ftp-lab/actions/workflows/mirror.yml)
[![Pipeline en GitLab](https://gitlab.com/BENDER_5000/ftp-lab/badges/-/pipeline.svg)](https://gitlab.com/BENDER_5000/ftp-lab/-/pipelines)

Cliente FTP interactivo **multiplataforma (Windows / Linux / macOS)** y servidor local opcional, pensados para **aprender ciberseguridad en tu propia red**. Todo está escrito con la biblioteca estándar de Python (el cliente no tiene dependencias externas).

> ⚠️ **Aviso ético y legal:** usa esta herramienta **únicamente contra equipos propios o con autorización explícita**. El FTP clásico envía usuario y contraseña en texto plano. No lo utilices en sistemas de terceros ni para escanear, explotar o acceder sin permiso. Esto es un laboratorio didáctico, no una herramienta de ataque.

## Contenido

| Archivo | Descripción |
|---|---|
| `ftp_lab.py` | Cliente FTP/FTPS interactivo (comandos tipo `ftp` clásico). |
| `lab_server.py` | Servidor FTP local para practicar (requiere `pyftpdlib`). |
| `profiles.ini.example` | Ejemplo de perfiles de conexión. |
| `docs/GUIA_DIDACTICA_ES.md` | Guía didáctica en español. |
| `docs/TEACHING_GUIDE_EN.md` | Teaching guide in English. |
| `docs/GUIA_DIDACTICA_AST.md` | Guía didáctica n'asturianu (bable). |
| `.github/workflows/mirror.yml` | Espejo automático GitHub → GitLab. |
| `.gitlab-ci.yml` | Espejo automático GitLab → GitHub. |
| `scripts/verify_mirror.sh` | Comprobación de que ambos espejos están sincronizados. |

## Instalación

Necesitas **Python 3.8 o superior**.

**Linux / macOS**
```bash
git clone https://github.com/BENDER35/ftp-lab.git
cd ftp-lab
python3 -m pip install -r requirements-dev.txt   # solo para el servidor local
```

**Windows (PowerShell)**
```powershell
git clone https://github.com/BENDER35/ftp-lab.git
cd ftp-lab
py -m pip install -r requirements-dev.txt        # solo para el servidor local
```

El cliente `ftp_lab.py` **no necesita instalar nada**.

## Inicio rápido

### 1. Levantar el servidor de prácticas (solo localhost)

```bash
python3 lab_server.py --root ./ftp_root --user labuser --password labpass --allow-write
```

Por defecto escucha en `127.0.0.1:2121` y **no es accesible desde fuera**. Para probar desde otro equipo de tu red local añade `--allow-lan` (el servidor pasa a escuchar en `0.0.0.0`). No lo expongas a Internet.

### 2. Conectar con el cliente

```bash
python3 ftp_lab.py --host 127.0.0.1 --port 2121 --user labuser --password labpass
```

Si omites `--password`, se te pedirá de forma segura. Dentro del cliente:

```
ftp:labuser@127.0.0.1> help
ftp:labuser@127.0.0.1> pwd
ftp:labuser@127.0.0.1> ls
ftp:labuser@127.0.0.1> mkdirPractica
ftp:labuser@127.0.0.1> put README.md README_copia.md
ftp:labuser@127.0.0.1> get README_copia.md
ftp:labuser@127.0.0.1> quit
```

### 3. Modo no interactivo y registro

```bash
python3 ftp_lab.py --host 127.0.0.1 --port 2121 --user labuser --password labpass \
  --command pwd --command ls --log sesion.log
```

### 4. Perfiles guardados

Copia `profiles.ini.example` a `profiles.ini`, edita los valores y conecta con:

```bash
python3 ftp_lab.py --profile laboratorio
```

### 5. FTPS (FTP sobre TLS)

Genera un certificado auto-firmado para el laboratorio:

```bash
openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem -days 30 -subj '/CN=localhost'
python3 lab_server.py --tls --cert cert.pem --key key.pem --allow-write
python3 ftp_lab.py --host 127.0.0.1 --port 2121 --user labuser --password labpass --secure --no-verify-ssl
```

`--no-verify-ssl` **solo** se usa con certificados auto-firmados propios; en un entorno real se debe verificar el certificado.

## Comandos del cliente

| Comando | Uso | Qué hace |
|---|---|---|
| `pwd` | `pwd` | Directorio actual en el servidor |
| `ls` / `dir` | `ls [ruta]` | Lista archivos |
| `cd` | `cd <ruta>` | Cambia de directorio |
| `get` | `get <remoto> [local]` | Descarga un archivo |
| `put` | `put <local> [remoto]` | Sube un archivo |
| `mkdir` / `rmdir` | `mkdir <nombre>` | Crea / borra directorios |
| `delete` | `delete <archivo>` | Borra un archivo remoto |
| `rename` | `rename <viejo> <nuevo>` | Renombra un archivo |
| `size` | `size <archivo>` | Muestra el tamaño |
| `binary` / `ascii` | `binary` | Modo de transferencia |
| `passive` / `active` | `passive` | Modo de conexión de datos |
| `status` / `debug` | `status` | Estado y depuración del protocolo |
| `quit` / `exit` / `bye` | `quit` | Cierra la sesión |

## Guías didácticas

- 🇪🇸 [Español](docs/GUIA_DIDACTICA_ES.md)
- 🇬🇧 [English](docs/TEACHING_GUIDE_EN.md)
- 🇪🇸 [Asturianu / bable](docs/GUIA_DIDACTICA_AST.md)

## Espejo bidireccional GitHub ⇄ GitLab

- GitHub → GitLab: `.github/workflows/mirror.yml` (push en cualquier rama o tag).
- GitLab → GitHub: `.gitlab-ci.yml` (push en cualquier rama o tag).
- Ambos usan `git push --mirror`. Cuando los repositorios ya están igualados el push es un **no-op**, por lo que **no hay bucles infinitos**.
- Secretos necesarios: `GITLAB_TOKEN` en GitHub (con `write_repository`) y `GH_TOKEN` en GitLab (con `repo`).

Comprobar la sincronización:

```bash
bash scripts/verify_mirror.sh
```

Repositorios: [GitHub](https://github.com/BENDER35/ftp-lab) · [GitLab](https://gitlab.com/BENDER_5000/ftp-lab)

## Licencia

[MIT](LICENSE). Uso didáctico y autorizado exclusivamente.
