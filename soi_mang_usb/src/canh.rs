//! canh.rs — TANG 3: canh gac & (tuy chon) chan.
//!
//! Muc tieu phong thu that su cua ban: KHONG phai soi tung nguoi, ma la BIET NGAY
//! khi co may LA nhay vao wifi. Cach lam:
//!   - Giu mot danh sach MAC "da biet" (whitelist) trong `danh_biet.txt`.
//!   - Quet dinh ky. May nao co MAC KHONG trong danh sach = LA → bao dong.
//!   - Tuy chon `--chan`: gui ARP "ho tang" khien may la tuong gateway o mot MAC chet
//!     → cat Internet cua no. (Chi dung tren mang ban so huu.)
//!
//! Cach chan AN TOAN & ben nhat van la loc MAC tren router. `--chan` chi la bien phap
//! tam khi ban chua vao duoc router.

use crate::arp::{self, dong_arp_reply};
use crate::bat_tri::BaTri;
use crate::mac::Mac;
use crate::nic::Nic;
use std::collections::HashSet;
use std::io::Write;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;

/// Doc 1 MAC dang "aa:bb:cc:dd:ee:ff".
pub fn doc_mac(s: &str) -> Option<Mac> {
    let p: Vec<&str> = s.trim().split(':').collect();
    if p.len() != 6 {
        return None;
    }
    let mut m = [0u8; 6];
    for i in 0..6 {
        m[i] = u8::from_str_radix(p[i], 16).ok()?;
    }
    Some(Mac(m))
}

/// Nap whitelist tu file (moi dong 1 MAC; dong '#' la chu thich).
pub fn nap_whitelist(duong: &str) -> HashSet<Mac> {
    let mut ds = HashSet::new();
    if let Ok(nd) = std::fs::read_to_string(duong) {
        for dong in nd.lines() {
            let d = dong.trim();
            if d.is_empty() || d.starts_with('#') {
                continue;
            }
            // cho phep "mac  # ghi chu"
            let mac_phan = d.split('#').next().unwrap_or(d).trim();
            if let Some(m) = doc_mac(mac_phan) {
                ds.insert(m);
            }
        }
    }
    ds
}

/// Ghi whitelist ban dau (baseline) — moi may dang thay = tam coi la "biet".
pub fn ghi_baseline(duong: &str, thay: &std::collections::BTreeMap<[u8; 4], arp::MayThay>) {
    let mut s = String::from("# danh_biet.txt — MAC cac may BAN BIET (baseline tu lan quet dau).\n# Xoa dong nao neu do KHONG phai may cua ban → lan sau no se bi bao LA.\n");
    for (_ip, m) in thay {
        s.push_str(&format!("{}  # {}\n", m.mac, ip_str(m.ip)));
    }
    let _ = std::fs::write(duong, s);
}

fn ip_str(ip: [u8; 4]) -> String {
    format!("{}.{}.{}.{}", ip[0], ip[1], ip[2], ip[3])
}

/// Vong CANH: quet moi `chu_ky` giay, bao dong may LA. `dang_chay` ha → dung.
pub fn canh<N: Nic>(
    nic: &N,
    chu_ky_giay: u64,
    chan: bool,
    dang_chay: Arc<AtomicBool>,
) -> std::io::Result<()> {
    let duong_wl = "danh_biet.txt";
    let mut whitelist = nap_whitelist(duong_wl);

    // Lan quet dau lam baseline neu chua co whitelist.
    if whitelist.is_empty() {
        eprintln!("[canh] chua co danh_biet.txt → quet lan dau lam BASELINE...");
        let thay = arp::quet(nic, 3000)?;
        ghi_baseline(duong_wl, &thay);
        whitelist = thay.values().map(|m| m.mac).collect();
        eprintln!(
            "[canh] da ghi {} MAC vao danh_biet.txt. HAY MO FILE, xoa dong nao khong phai may ban.",
            whitelist.len()
        );
    }
    eprintln!(
        "[canh] gac moi {}s · {} MAC da biet · chan={}",
        chu_ky_giay,
        whitelist.len(),
        chan
    );

    // Gateway (de chan): doan .1
    let mut gw_ip = nic.ipv4();
    gw_ip[3] = 1;
    let mac_chet = Mac([0xde, 0xad, 0x00, 0x00, 0x00, 0x01]); // MAC "chet" de ho tang

    let mut da_bao: HashSet<Mac> = HashSet::new();
    while dang_chay.load(Ordering::SeqCst) {
        let thay = arp::quet(nic, 2500)?;
        let mut la = 0u32;
        for (_ip, m) in &thay {
            if !whitelist.contains(&m.mac) {
                la += 1;
                let moi = da_bao.insert(m.mac); // true = lan dau thay ke la nay
                let dau = if moi { "!!! LA MOI" } else { "    van la" };
                println!(
                    "  {} {} {}  {}",
                    dau,
                    ip_str(m.ip),
                    m.mac,
                    if m.mac.la_cuc_bo() { "(MAC ngau nhien)" } else { "" }
                );
                if moi {
                    ghi_bao_dong(m.ip, m.mac);
                }
                if chan {
                    // Ho tang: bao ke la rang gateway o MAC chet → cat mang no.
                    let doi = dong_arp_reply(mac_chet, gw_ip, m.mac, m.ip);
                    for _ in 0..3 {
                        let _ = nic.gui(&doi);
                    }
                }
            }
        }
        if la == 0 {
            println!("  [{}] yen — khong may la. ({} may biet dang SANG)", nhip(), thay.len());
        }

        // Ngu het chu_ky nhung van nhay Ctrl-C.
        let het = std::time::Instant::now() + Duration::from_secs(chu_ky_giay);
        while std::time::Instant::now() < het && dang_chay.load(Ordering::SeqCst) {
            std::thread::sleep(Duration::from_millis(200));
        }
    }
    eprintln!("[canh] dung.");
    Ok(())
}

fn nhip() -> &'static str {
    "gac"
}

fn ghi_bao_dong(ip: [u8; 4], mac: Mac) {
    if let Ok(mut f) = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open("canh_bao.jsonl")
    {
        let _ = writeln!(
            f,
            "{{\"ip\":\"{}\",\"mac\":\"{}\",\"trang_thai\":\"{}\",\"su_kien\":\"may_la\"}}",
            ip_str(ip),
            mac,
            BaTri::Sang.ten()
        );
    }
}
