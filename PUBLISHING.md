# Panduan Publish: ssyubix-pixelart-mcp

Langkah-langkah ini butuh kredensial pribadi kamu (token PyPI, login GitHub
OAuth interaktif), jadi harus dijalankan sendiri di terminal lokal — bukan
sesuatu yang bisa saya jalankan dari sini.

## 0. Lisensi — sudah selesai

Proyek ini pakai **Apache License 2.0**. File `LICENSE` dan `NOTICE` sudah
dibuat, dan `pyproject.toml` sudah diisi `license = "Apache-2.0"`. Tidak ada
langkah tambahan di sini.

## 1. Push kode terbaru ke GitHub

```bash
cd ssyubix-pixelart-mcp   # folder hasil clone repo kamu
git add .
git commit -m "Rename project to ssyubix-pixelart-mcp, add 23 tools + publishing setup"
git push
```

## 2. Build paket Python

```bash
python -m pip install --upgrade build twine
python -m build
```
Ini menghasilkan `dist/ssyubix_pixelart_mcp-0.1.0-py3-none-any.whl` dan
`dist/ssyubix_pixelart_mcp-0.1.0.tar.gz`.

## 3. Upload ke PyPI

Buat API token dulu di https://pypi.org/manage/account/token/ (scope: seluruh
akun, atau khusus proyek ini setelah upload pertama). Lalu:

```bash
python -m twine upload dist/*
# Username: __token__
# Password: <tempel API token kamu>
```

Verifikasi: cek `https://pypi.org/project/ssyubix-pixelart-mcp/` — kalau nama
paket sudah dipakai orang lain, PyPI akan menolak upload dan kamu perlu ganti
nama (di `pyproject.toml`, `server.json`, dan README).

## 4. Install `mcp-publisher` CLI

```bash
git clone https://github.com/modelcontextprotocol/registry
cd registry
make publisher
# Binary ada di bin/mcp-publisher
```
(Cek juga halaman rilis resmi repo tersebut kalau-kalau sudah tersedia binary
siap pakai untuk platform kamu — saya belum verifikasi opsi itu secara detail.)

## 5. Autentikasi & publish ke MCP Registry

Kembali ke folder proyek (`server.json` sudah saya siapkan di root):

```bash
cd ssyubix-pixelart-mcp
/path/ke/registry/bin/mcp-publisher login github   # akan buka browser untuk OAuth GitHub
/path/ke/registry/bin/mcp-publisher publish
```

Autentikasi GitHub OAuth ini **harus** pakai akun `syuaibsyuaib` (username
GitHub kamu) karena namespace di `server.json` adalah
`io.github.syuaibsyuaib/ssyubix-pixelart-mcp` — harus cocok persis.

## 6. Verifikasi

```bash
curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.syuaibsyuaib/ssyubix-pixelart-mcp"
```
Kalau muncul di hasil JSON, publish berhasil.

## Update versi berikutnya

Setiap kali merilis versi baru: update `version` di `pyproject.toml` **dan**
`server.json` (harus sinkron), ulangi langkah 2-3 (build+upload PyPI), lalu
`mcp-publisher publish` ulang.

## Troubleshooting umum (dari dokumentasi resmi)

- **"Package validation failed"** → pastikan baris `<!-- mcp-name:
  io.github.syuaibsyuaib/ssyubix-pixelart-mcp -->` ada di README.md paket
  (sudah saya tambahkan) dan versi yang di-publish sama dengan versi yang
  ada di PyPI.
- **"Namespace not authorized"** → akun GitHub yang login ke `mcp-publisher`
  bukan `syuaibsyuaib`, atau nama di `server.json` tidak diawali
  `io.github.syuaibsyuaib/`.
