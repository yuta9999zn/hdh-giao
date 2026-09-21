//! oui.rs — tra HANG SAN XUAT tu 3 byte dau MAC.
//!
//! Day chinh la phan "thong tin cua ho" ma ban muon: MAC → hang may (Apple, Samsung,
//! TP-Link...). Luu y trung thuc: no cho biet HANG THIET BI, khong phai TEN NGUOI.
//!
//! Bang nho nhung IEEE thay doi lien tuc → co the nap them tu file `oui.txt` cua IEEE
//! (dinh dang "AABBCC   (base 16)   Ten Hang"). Chi mot vai OUI pho bien nhung o day
//! de tra ngay khong can mang.

use crate::mac::Mac;
use std::collections::HashMap;

/// Bang mam (seed) — vai hang rat pho bien tai gia dinh VN.
const MAM: &[(&[u8; 3], &str)] = &[
    (&[0x00, 0x1A, 0x11], "Google"),
    (&[0x3C, 0x5A, 0xB4], "Google"),
    (&[0xF4, 0xF5, 0xE8], "Google"),
    (&[0xAC, 0xDE, 0x48], "Apple"),
    (&[0xF0, 0x18, 0x98], "Apple"),
    (&[0x00, 0x1C, 0xB3], "Apple"),
    (&[0xDC, 0xA6, 0x32], "Raspberry Pi"),
    (&[0xB8, 0x27, 0xEB], "Raspberry Pi"),
    (&[0x50, 0xC7, 0xBF], "TP-Link"),
    (&[0xEC, 0x08, 0x6B], "TP-Link"),
    (&[0x00, 0x0E, 0x8F], "Xiaomi"),
    (&[0x28, 0x6C, 0x07], "Xiaomi"),
    (&[0x00, 0x12, 0xFB], "Samsung"),
    (&[0x8C, 0x77, 0x12], "Samsung"),
    (&[0x00, 0x1E, 0x10], "Huawei"),
    (&[0x00, 0x25, 0x9E], "Huawei"),
    (&[0x00, 0x50, 0x56], "VMware (may ao)"),
    (&[0x08, 0x00, 0x27], "VirtualBox (may ao)"),
    (&[0x00, 0x15, 0x5D], "Microsoft (Hyper-V/WSL)"),
    (&[0x00, 0x0D, 0x3A], "Microsoft"),
    (&[0x60, 0x45, 0xBD], "Microsoft"),
];

pub struct Oui {
    bang: HashMap<[u8; 3], String>,
}

impl Oui {
    pub fn moi() -> Oui {
        let mut bang = HashMap::new();
        for (k, v) in MAM {
            bang.insert(**k, v.to_string());
        }
        Oui { bang }
    }

    /// Nap them tu file oui.txt cua IEEE neu co (khong bat buoc).
    pub fn nap_file(&mut self, duong: &str) -> std::io::Result<usize> {
        let noi_dung = std::fs::read_to_string(duong)?;
        let mut them = 0;
        for dong in noi_dung.lines() {
            // dinh dang: "AC-DE-48   (hex)   Apple, Inc." hoac "ACDE48     (base 16)  Apple"
            if let Some(vt) = dong.find("(base 16)") {
                let phan_hex: String = dong[..vt]
                    .chars()
                    .filter(|c| c.is_ascii_hexdigit())
                    .collect();
                if phan_hex.len() >= 6 {
                    let b = |i: usize| u8::from_str_radix(&phan_hex[i..i + 2], 16).unwrap_or(0);
                    let key = [b(0), b(2), b(4)];
                    let ten = dong[vt + 9..].trim().to_string();
                    if !ten.is_empty() {
                        self.bang.insert(key, ten);
                        them += 1;
                    }
                }
            }
        }
        Ok(them)
    }

    /// Tra ten hang; neu MAC la ngau nhien (privacy) thi bao ro.
    pub fn tra(&self, mac: Mac) -> String {
        if mac.la_cuc_bo() {
            return "MAC-ngau-nhien (may dang giau danh tinh)".to_string();
        }
        match self.bang.get(&mac.oui()) {
            Some(t) => t.clone(),
            None => "hang-la".to_string(),
        }
    }
}
