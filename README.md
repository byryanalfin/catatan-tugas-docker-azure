# Catatan Tugas Kuliah — Docker pada Azure VM

Aplikasi praktikum Ryan Alfin Saputra (102062400072, kelas 07-02), menggunakan Flask, Gunicorn, dan PostgreSQL. Fitur: login, tambah tugas, tandai selesai, hapus tugas, dan ringkasan progres.

## Arsitektur

Browser → VM TCP 80 → app:8000 → database:5432.
App bergabung ke network frontend dan backend. Database hanya memakai backend dengan `internal: true` dan tidak mempublikasikan port. Data PostgreSQL berada pada named volume `postgres_data`. Kedua service memakai `restart: unless-stopped`. App menunggu database healthy.

## Menjalankan

1. Salin `.env.example` menjadi `.env`.
2. Ganti seluruh `CHANGE_ME` dengan nilai acak berbeda. Jangan commit `.env`.
3. Jalankan `docker compose up -d --build --wait`.
4. Buka `http://localhost/login` atau IP VM, lalu masuk dengan APP_USER dan APP_PASSWORD.

Dockerfile memakai dua tahap build untuk membuat wheel dependensi lalu memasangnya ke image runtime. Aplikasi berjalan sebagai user non-root. Endpoint `/health` memeriksa koneksi database.

## Deployment dan verifikasi

Diuji di VM Azure Ubuntu 24.04 x64, 8 GiB RAM, pada 26 Oktober 2026. Build dan pengujian container dilakukan langsung di VM. Pengujian lokal Docker belum dilakukan karena akses mesin Docker laptop tidak tersedia.

- Kedua service healthy.
- Data ditambah dari browser, lalu `docker compose down` dan `docker compose up -d --wait`; data tetap ada.
- Backend internal bernilai true; PortBindings database kosong.
- Kegagalan proses utama disimulasikan dengan SIGTERM; RestartCount naik 0 → 1 dan app kembali healthy.
- Login benar/salah, CSRF kosong, input kosong, tanggal invalid, dan logout diuji.

`docker stop` manual sengaja menghentikan container dan tidak menguji pemulihan otomatis `unless-stopped`. Gunakan kegagalan proses atau restart VM saat container berjalan. Jangan gunakan `docker compose down -v` jika data masih dibutuhkan.

## Operasi

```sh
docker compose ps
docker compose logs --tail=100 app
docker compose logs --tail=100 database
docker compose down
docker compose up -d --wait
```

HTTP digunakan sesuai tugas praktikum. Gunakan hanya data fiktif dan kredensial praktikum; untuk pemakaian nyata tambahkan HTTPS. Setelah bukti selesai, deallocate VM melalui Azure Portal agar komputasinya berhenti ditagih. Disk masih dapat dikenai biaya.

## Referensi

- https://docs.docker.com/compose/how-tos/startup-order/
- https://docs.docker.com/engine/containers/start-containers-automatically/
- https://www.psycopg.org/install/
