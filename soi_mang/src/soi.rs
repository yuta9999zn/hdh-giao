//! soi.rs — boc TEN MIEN tu goi di qua (khi dang `chen`).
//!
//! Su that quan trong: HTTPS ma hoa noi dung. Ta CHI lay duoc TEN MIEN, tu hai cho:
//!   - DNS query (UDP/53): may hoi "facebook.com o dau" → ta thay ten.
//!   - TLS SNI (TCP/443 ClientHello): ten mien nam RO (chua ma hoa) trong buoc bat tay.
//! Con NOI DUNG (tin nhan, mat khau) thi KHONG — do la gioi han that, khong phai thieu code.

/// Mot lan thay: ai (ip nguon) tra cuu / mo ten mien nao, qua dau.
pub struct LanSoi {
    pub nguon_ip: [u8; 4],
    pub ten_mien: String,
    pub qua: &'static str, // "dns" | "sni"
}

fn ipv4_header(khung: &[u8]) -> Option<(usize, u8, [u8; 4], [u8; 4])> {
    if khung.len() < 34 {
        return None;
    }
    if u16::from_be_bytes([khung[12], khung[13]]) != 0x0800 {
        return None; // khong phai IPv4
    }
    let ihl = (khung[14] & 0x0f) as usize * 4;
    if ihl < 20 || 14 + ihl > khung.len() {
        return None;
    }
    let proto = khung[23];
    let src = [khung[26], khung[27], khung[28], khung[29]];
    let dst = [khung[30], khung[31], khung[32], khung[33]];
    Some((14 + ihl, proto, src, dst))
}

/// Doc 1 khung, tra ve lan soi neu boc duoc ten mien.
pub fn soi_khung(khung: &[u8]) -> Option<LanSoi> {
    let (l4, proto, src, _dst) = ipv4_header(khung)?;

    if proto == 17 {
        // UDP
        if l4 + 8 > khung.len() {
            return None;
        }
        let dport = u16::from_be_bytes([khung[l4 + 2], khung[l4 + 3]]);
        if dport == 53 {
            let payload = &khung[l4 + 8..];
            if let Some(ten) = ten_tu_dns(payload) {
                return Some(LanSoi { nguon_ip: src, ten_mien: ten, qua: "dns" });
            }
        }
    } else if proto == 6 {
        // TCP
        if l4 + 20 > khung.len() {
            return None;
        }
        let data_off = ((khung[l4 + 12] >> 4) as usize) * 4;
        let dport = u16::from_be_bytes([khung[l4 + 2], khung[l4 + 3]]);
        let tt = l4 + data_off; // dau payload TCP
        if dport == 443 && tt < khung.len() {
            if let Some(ten) = sni_tu_tls(&khung[tt..]) {
                return Some(LanSoi { nguon_ip: src, ten_mien: ten, qua: "sni" });
            }
        }
    }
    None
}

/// Boc ten mien tu 1 DNS query (chi lay cau hoi dau).
fn ten_tu_dns(p: &[u8]) -> Option<String> {
    if p.len() < 12 {
        return None;
    }
    let qd = u16::from_be_bytes([p[4], p[5]]);
    if qd == 0 {
        return None;
    }
    let mut i = 12;
    let mut nhan = String::new();
    while i < p.len() {
        let len = p[i] as usize;
        if len == 0 {
            break;
        }
        if len & 0xc0 != 0 {
            return None; // con tro nen — bo qua cho gon
        }
        i += 1;
        if i + len > p.len() {
            return None;
        }
        if !nhan.is_empty() {
            nhan.push('.');
        }
        for &b in &p[i..i + len] {
            nhan.push(b as char);
        }
        i += len;
    }
    if nhan.is_empty() {
        None
    } else {
        Some(nhan)
    }
}

/// Boc SNI tu TLS ClientHello (khong ma hoa). Tra ten mien host.
fn sni_tu_tls(p: &[u8]) -> Option<String> {
    // TLS record: type(1)=0x16 handshake, ver(2), len(2)
    if p.len() < 5 || p[0] != 0x16 {
        return None;
    }
    let mut i = 5;
    // Handshake: type(1)=0x01 ClientHello, len(3)
    if i + 4 > p.len() || p[i] != 0x01 {
        return None;
    }
    i += 4;
    // ver(2) + random(32)
    i += 2 + 32;
    if i >= p.len() {
        return None;
    }
    // session id
    let sid = *p.get(i)? as usize;
    i += 1 + sid;
    // cipher suites
    if i + 2 > p.len() {
        return None;
    }
    let cs = u16::from_be_bytes([p[i], p[i + 1]]) as usize;
    i += 2 + cs;
    // compression methods
    if i >= p.len() {
        return None;
    }
    let cm = p[i] as usize;
    i += 1 + cm;
    // extensions
    if i + 2 > p.len() {
        return None;
    }
    let mut ext_het = i + 2 + u16::from_be_bytes([p[i], p[i + 1]]) as usize;
    i += 2;
    ext_het = ext_het.min(p.len());
    while i + 4 <= ext_het {
        let et = u16::from_be_bytes([p[i], p[i + 1]]);
        let el = u16::from_be_bytes([p[i + 2], p[i + 3]]) as usize;
        i += 4;
        if et == 0x0000 {
            // server_name extension
            // server_name_list len(2) + type(1)=0 + name_len(2) + name
            if i + 5 > p.len() {
                return None;
            }
            let nl = u16::from_be_bytes([p[i + 3], p[i + 4]]) as usize;
            let bd = i + 5;
            if bd + nl > p.len() {
                return None;
            }
            return Some(p[bd..bd + nl].iter().map(|&b| b as char).collect());
        }
        i += el;
    }
    None
}
