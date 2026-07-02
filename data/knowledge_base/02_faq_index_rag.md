# FAQ Index untuk RAG - Custom 3D Printing

> File ini adalah TURUNAN dari 01_SOP_kebijakan_3dprinting.md, khusus dibuat buat di-embed ke vector database sebagai index retrieval. JANGAN edit manual di sini kalau ada kebijakan berubah — edit di file SOP, terus generate ulang file ini.
>
> Format: satu Q&A = satu chunk. Setiap chunk punya tag [source: <bagian SOP>] biar bisa ditrace balik ke SOP kalau perlu audit/update.

---

[source: Kebijakan Harga]
Q: Berapa harga print per gram?
A: PLA Rp300/gram, PETG Rp350/gram, ABS Rp350/gram, Resin Rp1.500/gram.

[source: Kebijakan Harga]
Q: Ada minimum order?
A: Ada, minimum charge Rp50.000 per order meskipun berat hasil print di bawah itu.

[source: Kebijakan Harga]
Q: Infill ngaruh ke harga ga?
A: Ngaruh. Default infill 20%, makin tinggi infill makin berat hasilnya jadi harga naik proporsional.

[source: Kebijakan Harga]
Q: Ada biaya tambahan kalau desain butuh banyak support?
A: Ada tambahan 10-20% dari harga dasar untuk desain dengan support material banyak.

[source: Kebijakan Harga]
Q: Berapa biaya jasa desain 3D dari nol?
A: Mulai Rp100.000, tergantung tingkat kompleksitas objek.

[source: Kebijakan Harga]
Q: Berapa biaya finishing seperti cat atau sanding?
A: Mulai Rp50.000, tergantung ukuran objek dan tingkat detail.

[source: Kebijakan Harga]
Q: Konsultasi desain sebelum order bayar ga?
A: Gratis, dibatasi 1 sesi per calon customer.

[source: Kebijakan Harga]
Q: Ongkir ditanggung siapa?
A: Ditanggung customer, dihitung otomatis sesuai ekspedisi dan lokasi tujuan.

[source: Kebijakan Waktu Pengerjaan]
Q: Berapa lama proses print barang kecil?
A: 1-2 hari kerja untuk objek di bawah 10cm.

[source: Kebijakan Waktu Pengerjaan]
Q: Berapa lama proses print barang besar atau multi-part?
A: 3-7 hari kerja.

[source: Kebijakan Waktu Pengerjaan]
Q: Kalau lagi ramai order, waktu produksi bisa molor?
A: Bisa nambah 1-3 hari kerja dari estimasi normal saat masa antrian ramai.

[source: Kebijakan Waktu Pengerjaan]
Q: Ada opsi rush order atau produksi cepat?
A: Ada, tambahan biaya 50% dari harga normal, target next day (tidak berlaku untuk objek besar/multi-part).

[source: Kebijakan Waktu Pengerjaan]
Q: Kalau perlu revisi desain dulu, nambah waktu berapa lama?
A: Nambah estimasi 1-2 hari kerja dari waktu produksi normal.

[source: Kebijakan Waktu Pengerjaan]
Q: Berapa total waktu dari order sampai barang diterima?
A: 3-10 hari kerja, tergantung kompleksitas produksi ditambah waktu tempuh ekspedisi.

[source: Kapasitas & Batasan Ukuran Print]
Q: Berapa ukuran maksimal yang bisa diprint?
A: Build volume maksimal 25cm x 25cm x 25cm.

[source: Kapasitas & Batasan Ukuran Print]
Q: Kalau barang lebih besar dari kapasitas mesin gimana?
A: Dipecah jadi beberapa part, lalu disambung pakai lem khusus atau sistem dowel/pin.

[source: Kapasitas & Batasan Ukuran Print]
Q: Seberapa presisi toleransi ukuran hasil print?
A: Toleransi standar +/- 0.2mm dari ukuran file asli, detail minimal sekitar 0.4mm.

[source: Material & Finishing]
Q: Material apa aja yang tersedia?
A: PLA, PETG, ABS, TPU (fleksibel), dan Resin.

[source: Material & Finishing]
Q: Material apa yang cocok buat outdoor atau tahan benturan?
A: PETG atau ABS, lebih tahan panas dan benturan dibanding PLA.

[source: Material & Finishing]
Q: Bisa pilih warna custom?
A: Bisa pilih dari stok warna yang tersedia. Warna custom di luar stok kena biaya tambahan mixing/order khusus.

[source: Material & Finishing]
Q: Hasil print ada garis-garis kelihatan ga?
A: Hasil FDM (PLA/PETG/ABS/TPU) tanpa finishing menunjukkan garis layer yang terlihat. Resin hasilnya lebih halus tapi lebih rapuh.

[source: Material & Finishing]
Q: Beda resin sama FDM apa?
A: FDM lebih kuat dan murah, cocok fungsi umum. Resin lebih detail dan halus tapi lebih gampang patah dan lebih mahal.

[source: Proses Pemesanan & File Desain]
Q: Format file yang diterima apa aja?
A: STL, OBJ, dan STEP.

[source: Proses Pemesanan & File Desain]
Q: Belum punya file 3D, bisa dibuatin dari foto?
A: Bisa, minimal kirim foto dari 3 sudut (depan, samping, atas) dengan objek pembanding ukuran seperti penggaris atau koin.

[source: Proses Pemesanan & File Desain]
Q: Gimana alur jasa desain custom dari nol?
A: Konsultasi konsep dulu, DP 50%, lalu preview 3D untuk approval, baru lanjut produksi.

[source: Proses Pemesanan & File Desain]
Q: Berapa kali revisi desain gratis?
A: 2x revisi gratis, revisi ke-3 dan seterusnya kena Rp25.000 per revisi.

[source: Proses Pemesanan & File Desain]
Q: Cara kirim file gimana?
A: Bisa langsung via chat WhatsApp atau share link Google Drive.

[source: Pembayaran]
Q: Metode pembayaran apa aja yang bisa dipakai?
A: Transfer bank, e-wallet (OVO/DANA/GoPay), dan QRIS.

[source: Pembayaran]
Q: Wajib DP dulu?
A: Wajib, DP 50% di awal sebelum produksi dimulai.

[source: Pembayaran]
Q: Pelunasan kapan?
A: Sebelum barang dikirim atau diambil customer.

[source: Pembayaran]
Q: Ada invoice resmi?
A: Ada, dikirim via WhatsApp setelah pembayaran dikonfirmasi.

[source: Revisi, Garansi & Komplain]
Q: Kalau hasil print cacat gimana?
A: Reprint gratis kalau terbukti cacat dari kesalahan produksi, bukan kesalahan desain dari customer.

[source: Revisi, Garansi & Komplain]
Q: Berapa lama garansi reprint berlaku?
A: 3 hari sejak barang diterima customer.

[source: Revisi, Garansi & Komplain]
Q: Batas waktu komplain berapa lama?
A: Maksimal 2x24 jam setelah barang diterima, dengan menyertakan foto bukti.

[source: Pengiriman & Pengambilan]
Q: Bisa COD atau ambil langsung?
A: Bisa COD untuk area tertentu, atau ambil langsung di workshop.

[source: Pengiriman & Pengambilan]
Q: Pakai ekspedisi apa?
A: JNE, J&T, dan SiCepat.

[source: Pengiriman & Pengambilan]
Q: Packingnya gimana biar aman?
A: Bubble wrap dan dus, part kecil/detail dipacking terpisah dalam dus kecil tambahan.

[source: Pengiriman & Pengambilan]
Q: Ada opsi gift wrap?
A: Ada, tambahan biaya Rp15.000.

[source: Diskon & Bulk Order]
Q: Ada diskon buat order banyak?
A: Diskon 10% untuk order di atas 10pcs, dan 15% untuk di atas 50pcs.

[source: Diskon & Bulk Order]
Q: Ada harga khusus reseller?
A: Ada, dengan syarat minimal order rutin bulanan, negosiasi langsung dengan admin.

[source: Diskon & Bulk Order]
Q: Ada promo musiman?
A: Ada, biasanya diskon 20% saat momen lebaran dan natal.

[source: Ketentuan Umum Lainnya]
Q: Lokasi workshop di mana?
A: Jl. Contoh Raya No. 12, Purwokerto, Jawa Tengah.

[source: Ketentuan Umum Lainnya]
Q: Bisa lihat portofolio hasil kerja?
A: Bisa, cek Instagram @dummy3dprint.studio.

[source: Ketentuan Umum Lainnya]
Q: Jam operasional CS jam berapa?
A: Setiap hari pukul 09.00-21.00 WIB.

[source: Ketentuan Umum Lainnya]
Q: Bisa print karakter berlisensi kayak dari film/game?
A: Bisa untuk penggunaan personal, tapi tidak dilayani untuk reproduksi komersial tanpa izin resmi dari pemegang lisensi.

[source: Ketentuan Umum Lainnya]
Q: Ada minimum order quantity?
A: Tidak ada MOQ untuk retail satuan. MOQ untuk harga diskon bulk dimulai dari 10pcs.

[source: Ketentuan Umum Lainnya]
Q: Bisa print buat fungsi teknis kayak gear atau bracket?
A: Bisa, disarankan pakai PETG atau ABS untuk kekuatan lebih baik, tidak disarankan untuk beban struktural berat.
