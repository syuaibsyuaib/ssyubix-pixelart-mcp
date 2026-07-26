# Task: ssyubix-pixelart-mcp (nama internal modul tetap pixelart_mcp)

MCP server (Python, FastMCP, stdio) untuk menggambar pixel art & menyusun
tileset game 2D, dirancang untuk berjalan berdampingan dengan
`unity-mcp-server` (ekspor PNG + metadata JSON siap slice/import).

## Status: 23 tools, 58 unit test PASS, siap review pengguna

## Selesai
- [x] Riset SDK resmi (MCP Python SDK v1.x stable, pin `mcp>=1.27,<2`; v2 masih pre-release, dihindari untuk produksi)
- [x] `canvas.py` — primitif gambar piksel (set_pixel, draw_line/rect/circle/polygon, flood_fill, flip, duplicate, preview upscale, extract_palette, info, from_file/import)
- [x] `palette.py` — generator palet prosedural (8 preset gaya + fallback golden-ratio hue spacing)
- [x] `sizing.py` — heuristik saran ukuran tile (default 16 PPU, kategori objek, atau resolusi layar)
- [x] `tileset.py` — assembly grid tile + export PNG & metadata JSON
- [x] `models.py` — semua Pydantic input model (23 tools)
- [x] `server.py` — 23 MCP tools terdaftar dengan annotations lengkap:
      drawing (create_canvas, import_canvas, set_pixel, draw_line/rect/circle/polygon, flood_fill),
      canvas management (clear, flip, duplicate, get_info, get_preview, delete, list),
      palette (generate, extract), sizing (suggest_tile_size),
      tileset (create, set_tile, export, delete, list)
- [x] `pixelart_import_canvas` — load PNG existing dari disk ke canvas (edit sprite yang sudah ada, bukan gambar dari nol)
- [x] Unit test: 58 test (canvas, palette, sizing, tileset, management tools, integrasi server) — semua PASS
- [x] Smoke test protokol MCP in-memory (list_tools + call_tool) — berhasil, 23 tools terverifikasi
- [x] `AGENTS.md` — panduan untuk AI agent yang merawat/mengembangkan proyek: peta arsitektur, konvensi wajib, checklist tambah tool, alur menangani kritik/permintaan fitur
- [x] Panduan fallback manual import ke Unity Editor (tanpa `unity-mcp-server`) di README.md, berdasarkan Unity Manual resmi (Grid By Cell Size, PPU, Filter Mode Point, Compression None)

## Belum / opsional (perlu konfirmasi pengguna)
- [ ] Testing nyata dengan `unity-mcp-server` (belum ada instalasi Unity di sandbox ini — perlu ditest di sisi pengguna)
- [ ] Streamable HTTP transport (saat ini hanya stdio; cukup untuk kebutuhan lokal saat ini)
- [ ] Kategori ukuran tile tambahan di luar 5 preset (small_prop, character, large_character, structure, large_structure)
- [ ] Style palet tambahan di luar 8 preset (forest, desert, ocean, retro, pastel, night, lava, candy)
- [ ] Undo/history per canvas — belum diminta, opsional

## Catatan desain penting
- Semua parameter teknis (ukuran, PPU) opsional dengan default cerdas —
  agar AI agent bisa melayani user non-teknis tanpa wajib menanyakan istilah teknis.
- State kanvas/tileset disimpan in-memory (dict) selama proses server hidup — cocok untuk stdio single-session.
- Pakai Pillow API non-deprecated (`get_flattened_data`) untuk hitung pixel, bukan `getdata()` yang deprecated per Pillow 14 (2027).

