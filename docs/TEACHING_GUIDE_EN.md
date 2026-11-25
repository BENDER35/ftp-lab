# Teaching guide: FTP lab

**Level:** beginner · **Estimated time:** 60–90 min · **Requirements:** Python 3.8+, a Linux or Windows machine, and permission to use your own local network.

> This guide teaches **how FTP works**. It is not about attacking systems. Everything runs against a server you control. Classic FTP sends credentials in cleartext, so keep the lab isolated.

## Learning objectives

By the end you will be able to:

1. Explain the difference between FTP's **control channel** and **data channel**.
2. Tell **active** (PORT) and **passive** (PASV) modes apart and explain why passive works better behind NAT/firewall.
3. Use a command-line FTP client to browse, upload and download files.
4. Read a protocol trace with `debug` and recognize reply codes (`220`, `230`, `150`, `226`, `530`...).
5. Compare FTP with FTPS and explain why encryption matters.
6. Apply hardening basics: dedicated user, no anonymous access, own password, no Internet exposure.

---

## Exercise 0 — Set up the lab

On the machine acting as **server**:

```bash
python3 -m pip install -r requirements-dev.txt
mkdir -p ftp_lab_root
python3 lab_server.py --root ./ftp_lab_root --user teacher --password 'LabPass_123' --allow-write --port 2121
```

On Windows use `py` instead of `python3`.

The server listens on `127.0.0.1:2121` by default. To connect **from another machine on your LAN**, add `--allow-lan` and note the server's local IP (`ip addr` on Linux, `ipconfig` on Windows).

**Question:** why does the server bind to `127.0.0.1` by default? *(Answer: so nobody else can reach it; `127.0.0.1` is the machine itself.)*

---

## Exercise 1 — First connection

From the client machine:

```bash
python3 ftp_lab.py --host 127.0.0.1 --port 2121 --user teacher --password 'LabPass_123'
```

Inside the client try:

```
pwd
ls
status
help
```

The prompt shows the current remote directory.

**Questions:**
- What does `status` say about TLS and passive mode?
- What error code do you get with a wrong password? (`530 Not logged in.`)

---

## Exercise 2 — Browse and transfer

```
mkdir Exercise2
cd Exercise2
ls
put README.md copy.md
ls
get copy.md downloaded.md
size copy.md
```

Check that `downloaded.md` exists locally and has the same size.

**Challenge:** create a local text file with one line, upload it, rename it with `rename`, then download it again.

**Concept:** `binary` sends bytes untouched; `ascii` converts line endings. Always use binary for images or archives. Our client uses binary for `get`/`put`.

---

## Exercise 3 — Watch the protocol

Connect with debugging enabled:

```bash
python3 ftp_lab.py --host 127.0.0.1 --port 2121 --user teacher --password 'LabPass_123' --debug 1
```

or type `debug 1` inside the session, then run `pwd`, `ls`, `quit`.

You will see something like:

```
> USER teacher
< 331 Password required
> PASS ...
< 230 User logged in, proceed
> PWD
< 257 "/" is the current directory
```

Match these codes:

| Code | Meaning |
|---|---|
| `220` | Service ready |
| `331` | Password required |
| `230` | Login successful |
| `257` | Current pathname |
| `150` | Data connection open |
| `226` | Transfer complete |
| `530` | Not authorized |
| `550` | File not found / action not allowed |

**Question:** which commands open a new data connection? *(LIST and RETR/STOR.)*

---

## Exercise 4 — Active vs passive

1. In **passive** mode (default) run `ls`. It works.
2. Type `active` and run `ls` again.

Active mode makes the server connect back to a client port; a firewall or NAT usually blocks it. Passive mode is the norm today.

**Question:** why does passive mode work better behind a home router? *(Because the client initiates both connections toward the server.)*

---

## Exercise 5 — FTPS

Generate a self-signed certificate on the server:

```bash
openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem -days 30 -subj '/CN=localhost'
python3 lab_server.py --tls --cert cert.pem --key key.pem --port 2121 --allow-write
```

Connect from the client:

```bash
python3 ftp_lab.py --host 127.0.0.1 --user teacher --password 'LabPass_123' --secure --no-verify-ssl --debug 1
```

Look for `AUTH TLS` and `PBSZ`/`PROT` in the trace. Compare with Exercise 3: the password is no longer in cleartext.

**Question:** why is `--no-verify-ssl` fine here but not in production? *(Because the certificate is our own self-signed one; production must validate the trust chain.)*

---

## Exercise 6 — Logging and analysis

```bash
python3 ftp_lab.py --host 127.0.0.1 --user teacher --password 'LabPass_123' --log session.log --command pwd --command ls
cat session.log
```

The log stores **commands and responses**, never the password. Use it to document your work.

---

## Exercise 7 — Hardening checklist

- [ ] Dedicated user, no `anonymous`.
- [ ] Long, lab-specific password.
- [ ] Root restricted to one directory (`--root`).
- [ ] Read-only unless write is needed (drop `--allow-write`).
- [ ] Bind to `127.0.0.1` unless LAN access is required.
- [ ] FTPS (`--tls`) when practising encryption.
- [ ] No port forwarding, no Internet exposure.
- [ ] For a real service, prefer **SFTP** (SSH) over FTP.

---

## Golden rules

1. **Your own machine only, or with explicit written permission.**
2. Do not scan or guess credentials on networks you do not own.
3. Never store real passwords in `profiles.ini`.
4. Stop the server with Ctrl+C when finished.
5. If something looks wrong, stop and ask your teacher or mentor.

## Next step

Read the bidirectional mirror section in the [README](../README.md) and practise `git push` / `git pull` to see GitHub and GitLab stay in sync.
