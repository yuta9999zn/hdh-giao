//! arp.rs — dong/doc goi ARP, va bo QUET (Tang 1).
//!
//! Nguyen ly (hoc tu arp-scan, KHONG be nguyen):
//!   ARP la cach may hoi "ai giu IP nay? cho toi MAC". Trong LAN, moi may PHAI
//!   tra loi ARP that de nhan duoc goi — nen ARP kho giau hon ping (ICMP co the bi
//!   firewall nuot im). Ta gui ARP request cho tung IP trong dai; ai reply = SANG.

use crate::mac::Mac;
use crate::nic::Nic;
use crate::bat_tri::BaTri;
use std::collections::BTreeMap;
use std::io;
use std::time::{Duration, Instant};

const ETH_TYPE_ARP: u16 = 0x0806;
const HW_ETHERNET: u16 = 1;
const PROTO_IPV4: u16 = 0x0800;
const OP_REQUEST: u16 = 1;
const OP_REPLY: u16 = 2;

/// Dong 1 khung Ethernet + ARP request: "ai giu `dich`? tra ve cho toi".
pub fn dong_arp_request(cua_toi_mac: Mac, cua_toi_ip: [u8; 4], dich_ip: [u8; 4]) -> Vec<u8> {
    let mut k = Vec::with_capacity(42);
    // -- Ethernet header (14 byte) --
    k.extend_from_slice(&Mac::QUANG_BA.0); // dich: quang ba (hoi ca mang)
    k.extend_from_slice(&cua_toi_mac.0); // nguon
    k.extend_from_slice(&ETH_TYPE_ARP.to_be_bytes());
    // -- ARP (28 byte) --
    k.extend_from_slice(&HW_ETHERNET.to_be_bytes());
    k.extend_from_slice(&PROTO_IPV4.to_be_bytes());
    k.push(6); // hlen
    k.push(4); // plen
    k.extend_from_slice(&OP_REQUEST.to_be_bytes());
    k.extend_from_slice(&cua_toi_mac.0); // sender MAC
    k.extend_from_slice(&cua_toi_ip); // sender IP
    k.extend_from_slice(&Mac::ROI.0); // target MAC (chua biet = 0)
    k.extend_from_slice(&dich_ip); // target IP
    k
}

/// Dong ARP reply gia — dung cho `chen` (spoof): "IP `bao_ip` chinh la MAC cua toi".
pub fn dong_arp_reply(cua_toi_mac: Mac, bao_ip: [u8; 4], toi_mac: Mac, toi_ip: [u8; 4]) -> Vec<u8> {
    let mut k = Vec::with_capacity(42);
    k.extend_from_slice(&toi_mac.0); // dich
    k.extend_from_slice(&cua_toi_mac.0); // nguon (MAC that cua ta)
    k.extend_from_slice(&ETH_TYPE_ARP.to_be_bytes());
    k.extend_from_slice(&HW_ETHERNET.to_be_bytes());
    k.extend_from_slice(&PROTO_IPV4.to_be_bytes());
    k.push(6);
    k.push(4);
    k.extend_from_slice(&OP_REPLY.to_be_bytes());
    k.extend_from_slice(&cua_toi_mac.0); // sender MAC = MAC cua ta (day la loi noi doi)
    k.extend_from_slice(&bao_ip); // sender IP = IP ta gia lam (vd gateway)
    k.extend_from_slice(&toi_mac.0); // target MAC
    k.extend_from_slice(&toi_ip); // target IP
    k
}

/// Ket qua doc 1 ARP reply.
pub struct ArpReply {
    pub ip: [u8; 4],
    pub mac: Mac,
}

/// Doc khung: neu la ARP reply thi tra (ip nguon, mac nguon).
pub fn doc_arp_reply(khung: &[u8]) -> Option<ArpReply> {
    if khung.len() < 42 {
        return None;
    }
    // ethertype o byte 12..14
    if u16::from_be_bytes([khung[12], khung[13]]) != ETH_TYPE_ARP {
        return None;
    }
    let op = u16::from_be_bytes([khung[20], khung[21]]);
    if op != OP_REPLY {
        return None;
    }
    let mut m = [0u8; 6];
    m.copy_from_slice(&khung[22..28]); // sender MAC
    let ip = [khung[28], khung[29], khung[30], khung[31]]; // sender IP
    Some(ArpReply { ip, mac: Mac(m) })
}

/// Mot may thay duoc.
pub struct MayThay {
    pub ip: [u8; 4],
    pub mac: Mac,
    pub trang_thai: BaTri,
}

/// Tinh dai dia chi can quet tu ip + mat na (IPv4). Bo qua .0 (mang) va .255 (quang ba).
pub fn dai_dia_chi(ip: [u8; 4], mat_na: [u8; 4]) -> Vec<[u8; 4]> {
    let ip_u = u32::from_be_bytes(ip);
    let mask = u32::from_be_bytes(mat_na);
    let mang = ip_u & mask;
    let quang_ba = mang | !mask;
    let mut ds = Vec::new();
    let mut a = mang + 1;
    while a < quang_ba {
        ds.push(a.to_be_bytes());
        a += 1;
        if ds.len() > 65534 {
            break; // chan an toan cho mask qua rong
        }
    }
    ds
}

/// QUET (Tang 1): gui ARP request cho ca dai, gom reply trong `cho_ms` mili-giay.
/// Tra map ip→MayThay. May khong tra loi → khong xuat hien (tuc AN, ta khong bia).
pub fn quet<N: Nic>(nic: &N, cho_ms: u32) -> io::Result<BTreeMap<[u8; 4], MayThay>> {
    let toi_mac = nic.mac();
    let toi_ip = nic.ipv4();
    let dai = dai_dia_chi(toi_ip, nic.mat_na());

    // Ban het request truoc (nhanh), roi hut reply.
    for dich in &dai {
        if *dich == toi_ip {
            continue;
        }
        let khung = dong_arp_request(toi_mac, toi_ip, *dich);
        let _ = nic.gui(&khung); // loi le te 1 goi khong lam hong ca quet
    }

    let mut thay: BTreeMap<[u8; 4], MayThay> = BTreeMap::new();
    // THOI HAN CUNG: hut reply trong dung `cho_ms` mili-giay roi dung. KHONG dung "cho im lang"
    // (loi cu: mang BAN — vd co may choi game — thi khung tuon lien tuc, "im lang" khong bao gio
    // toi → vong quet TREO mai). Deadline cung thi luon ket thuc, du mang bao nhieu luu luong.
    let deadline = Instant::now() + Duration::from_millis(cho_ms as u64);
    while Instant::now() < deadline {
        match nic.nhan(200)? {
            Some(khung) => {
                if let Some(r) = doc_arp_reply(&khung) {
                    thay.entry(r.ip).or_insert(MayThay {
                        ip: r.ip,
                        mac: r.mac,
                        trang_thai: BaTri::Sang, // co reply = SANG
                    });
                }
            }
            None => {}
        }
    }
    Ok(thay)
}
