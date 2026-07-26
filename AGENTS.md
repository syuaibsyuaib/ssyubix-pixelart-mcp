# AGENTS.md — Panduan untuk AI Agent yang Merawat/Mengembangkan pixelart_mcp

Dokumen ini untuk AI (Claude atau lainnya) yang diminta menambah fitur baru,
memperbaiki bug, atau menindaklanjuti kritik pengguna terhadap server ini.
Baca ini dulu sebelum mengubah kode.

## Terminologi — WAJIB dipahami sebelum memakai tool sizing

Kesalahan yang sudah pernah terjadi di produksi: AI memanggil
`pixelart_suggest_tile_size`, dapat angka mis. 32x32, lalu langsung
membuat kanvas 32x32 itu dan menyerahkannya ke user sebagai "tilemap" —
hasilnya pecah/kekecilan karena 32x32 itu ukuran **satu tile**, bukan
ukuran gambar akhir. Definisi yang harus dipegang:

- **Tile**: satu ubin kecil (mis. 16x16px). Dibuat dengan `pixelart_create_canvas`.
- **Tileset**: lembar berisi banyak tile disusun dalam grid (mis. kumpulan
  jenis-jenis tile: rumput, jalan, air). Dibuat dengan `pixelart_create_tileset`
  + `pixelart_set_tile` per slot + `pixelart_export_tileset`.
- **Tilemap**: peta/level lengkap yang tersusun dari banyak tile — bisa
  berupa lembar besar hasil menempatkan tile berulang di tiap posisi grid
  (pakai `pixelart_create_tileset` dengan `columns`/`rows` = ukuran peta
  dalam satuan tile, lalu `pixelart_set_tile` untuk tiap posisi), ATAU
  representasi index array yang disusun di dalam game engine (misalnya
  Unity Tilemap component) menggunakan tileset yang sudah diekspor —
  **bukan** satu kanvas kecil seukuran satu tile.

Kalau user minta "tilemap" atau "peta/level", ALUR WAJIB:
1. `pixelart_suggest_tile_size` → dapat ukuran satu tile.
2. `pixelart_suggest_tilemap_layout` → dapat jumlah grid (columns/rows) dan
   ukuran total gambar dalam piksel, berdasarkan ukuran layar/level yang diinginkan.
3. `pixelart_create_tileset` dengan `columns`/`rows` dari langkah 2.
4. `pixelart_set_tile` untuk MENGISI SETIAP slot di grid tersebut (bukan cuma satu).
5. `pixelart_export_tileset`.

JANGAN PERNAH mengekspor kanvas tunggal seukuran satu tile dan menyebutnya
tilemap — itu persis bug yang membuat fitur ini ditambahkan.

## Peta arsitektur (di mana harus mengubah apa)

| File | Tanggung jawab | Ubah di sini kalau... |
|---|---|---|
| `canvas.py` | Primitif gambar piksel tunggal (`PixelCanvas`): set/get pixel, garis, bentuk, flood fill, flip, duplicate, palet, preview, info | ...permintaan soal *cara menggambar* satu tile (bentuk baru, operasi transformasi baru) |
| `palette.py` | Generator palet warna prosedural (`STYLE_PRESETS` + fallback) | ...permintaan soal *gaya/mood palet baru*, atau algoritma generate warna |
| `sizing.py` | Heuristik saran ukuran tile (`CATEGORY_BOXES`, base PPU) | ...permintaan soal *kategori objek baru* atau logika saran ukuran |
| `tileset.py` | Assembly grid tile jadi satu sheet + ekspor PNG/JSON (`Tileset`) | ...permintaan soal *format ekspor*, struktur metadata, atau assembly grid |
| `models.py` | Semua Pydantic input model, satu per tool | ...menambah/mengubah parameter tool apa pun (WAJIB, lihat di bawah) |
| `server.py` | Registrasi tool MCP (`@mcp.tool`), state in-memory (`_canvases`, `_tilesets`) | ...menambah tool baru atau mengubah cara tool dipanggil |
| `tests/` | Unit test per modul + integrasi | ...WAJIB ditambah/diupdate untuk setiap perubahan (lihat kebijakan testing) |

State (`_canvases`, `_tilesets`) adalah **dict in-memory**, hidup selama proses
server berjalan (stdio, single-session). Kalau ada permintaan fitur yang
mengasumsikan data tersimpan lintas restart server, itu di luar desain
saat ini — perlu didiskusikan dulu (lihat "Alur menangani permintaan fitur").

**Penting**: server ini dirancang tidak bergantung pada `unity-mcp-server`.
Semua tool tetap berfungsi penuh tanpanya — `pixelart_export_tileset` selalu
menulis PNG + JSON metadata ke disk terlebih dahulu, terlepas apakah agent
akan lanjut memanggil tool engine-integration atau tidak. Jangan menambahkan
kode yang memeriksa/mengasumsikan `unity-mcp-server` tersedia di dalam
`pixelart_mcp` itu sendiri — orkestrasi lintas-server itu tanggung jawab
agent, bukan server ini (lihat bagian "Jika unity-mcp-server tidak tersedia"
di README.md untuk panduan fallback manual yang sudah disiapkan untuk agent
sampaikan ke user).

## Konvensi wajib diikuti

1. **Nama proyek/distribusi PyPI/nama server MCP**: `ssyubix-pixelart-mcp`. Nama
   modul Python internal (folder yang di-`import`) tetap `pixelart_mcp` — ini
   pola umum (nama distribusi PyPI boleh beda dari nama modul). Jangan ubah
   nama modul internal tanpa alasan kuat, karena itu breaking change untuk
   siapa pun yang sudah `import pixelart_mcp`.
2. **Nama tool**: `pixelart_{action}_{resource}`, snake_case, action-oriented
   (`pixelart_draw_polygon`, bukan `polygon` atau `draw_polygon` tanpa prefix).
   Prefix tool ini independen dari nama proyek/distribusi di atas — jangan ikut
   diubah kalau nama proyek berubah lagi di masa depan, kecuali diminta eksplisit.
3. **Setiap tool** wajib punya:
   - Pydantic input model di `models.py` dengan `model_config = ConfigDict(extra="forbid")`
     dan `Field(..., description=...)` untuk tiap parameter.
   - `annotations={"title", "readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint"}`
     pada decorator `@mcp.tool`.
   - Docstring dengan `Args:` dan `Returns:` yang menjelaskan struktur JSON kalau tool
     mengembalikan JSON string.
4. **Error handling**: jangan `try/except` manual di tool function. Cukup
   `raise ValueError(...)` atau subclass-nya (`CanvasError`, `TilesetError`)
   dengan pesan yang jelas dan actionable — FastMCP otomatis mengubahnya jadi
   tool error result yang terlihat oleh agent pemanggil. Lihat `_get_canvas()`
   dan `_get_tileset()` di `server.py` sebagai contoh pesan error yang baik
   (menyebutkan tool apa yang harus dipanggil dulu).
5. **Parameter teknis harus punya default cerdas** (lihat `sizing.py`) —
   ingat, target pengguna akhir MCP ini termasuk gamer non-teknis yang
   dilayani oleh AI agent. Jangan buat parameter wajib yang berupa istilah
   teknis tanpa default.

## Cara menambah tool baru (checklist)

1. Implementasikan logika inti di modul domain yang sesuai (`canvas.py`/
   `palette.py`/`sizing.py`/`tileset.py`) — bukan langsung di `server.py`.
   `server.py` seharusnya cuma jadi lapisan tipis: validasi input (lewat
   Pydantic) → panggil modul domain → format return JSON/string/Image.
2. Tambah Pydantic input model di `models.py` (ikuti pola yang sudah ada).
3. Daftarkan tool baru di `server.py` dengan `@mcp.tool(...)` + docstring lengkap.
4. Tambah unit test di `tests/` — minimal: satu test "jalur normal", satu
   test error/edge case. Ikuti pola di `test_management_tools.py` atau
   `test_canvas.py`.
5. **Jalankan seluruh test suite** (`sh claude_tools/run_tests.sh` atau
   `python -m pytest pixelart_mcp/tests/ -v`) — semua harus PASS sebelum
   dianggap selesai.
6. Update tabel tools di `README.md` dan status di `task.md`.

## Cara menangani kritik/permintaan perubahan pada fitur yang sudah ada

1. **Klarifikasi dulu** kalau permintaan ambigu (mis. "warnanya kurang bagus" —
   tanya: kurang bagus untuk gaya apa? mau ubah preset yang ada atau
   tambah preset baru?).
2. **Jangan mengubah skema input tool yang sudah ada secara mengganggu (breaking)**
   tanpa alasan kuat — MCP client lain mungkin sudah bergantung padanya.
   Lebih aman: tambah parameter baru sebagai *optional dengan default*
   yang mempertahankan perilaku lama, daripada mengganti/menghapus parameter.
3. Kalau perubahan memang harus breaking (misalnya rename tool), sebutkan
   eksplisit ke pengguna bahwa ini breaking change dan minta konfirmasi
   sebelum menjalankannya (sesuai preferensi pengguna: konfirmasi sebelum
   melangkah jauh).
4. Setelah perbaikan, **jalankan ulang seluruh test suite**, bukan cuma test
   yang berkaitan dengan fitur yang diubah — untuk menangkap regresi.
5. Update `task.md` dengan status perubahan dan alasannya.

## Referensi SDK

Server ini pakai **MCP Python SDK v1.x (stable)**, bukan v2 (masih
pre-release per Juli 2026). Kalau butuh menambah fitur SDK-level baru
(resources, prompts, sampling, dsb), cek dulu dokumentasi resmi v1.x:
`https://github.com/modelcontextprotocol/python-sdk/blob/v1.x/docs/server.md`
— jangan mengandalkan ingatan/training data untuk API SDK, karena API ini
berubah antar versi.
