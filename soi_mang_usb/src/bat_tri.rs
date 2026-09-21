//! bat_tri.rs — BA-TRI cua GIAO: sang / toi / an.
//!
//! Day la linh hon triet ly GIAO, khong phai bit nhi phan. Mot may trong mang
//! khong chi "on/off" — no o mot trong ba the:
//!   - SANG : co tra loi (ARP reply ve) → chac chan dang online.
//!   - TOI  : bi chan / tu choi (vd co filter, hoac ta chu dong chan) → biet ro la KHONG.
//!   - AN   : chua ro — chua tra loi trong thoi han. KHONG dam ket luan la tat.
//!
//! Diem cot: 'an' lan truyen an toan (giong `null` bi diet trong GIAO). Mot may
//! im lang la AN chu khong phai TOI — ta khiem ton nhan thuc: chua hoi du thi chua biet.

use std::fmt;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum BaTri {
    Sang, // co mat, da tra loi
    Toi,  // vang mat co co so / bi chan
    An,   // chua ro
}

impl BaTri {
    /// Ky hieu 1 ky tu cho ban in nhanh.
    pub fn dau(&self) -> char {
        match self {
            BaTri::Sang => '+', // sang
            BaTri::Toi => '-',  // toi
            BaTri::An => '?',   // an
        }
    }

    /// Ten thuan Viet (khong dau) de ghi ra JSONL cho VM .giao doc.
    pub fn ten(&self) -> &'static str {
        match self {
            BaTri::Sang => "sang",
            BaTri::Toi => "toi",
            BaTri::An => "an",
        }
    }

    /// Hop nhat quan sat: mot lan thay SANG thi mai SANG (da chac co mat).
    /// TOI chi thang AN. AN khong lam mo di dieu da biet.
    pub fn hop(self, moi: BaTri) -> BaTri {
        match (self, moi) {
            (BaTri::Sang, _) | (_, BaTri::Sang) => BaTri::Sang,
            (BaTri::Toi, _) | (_, BaTri::Toi) => BaTri::Toi,
            _ => BaTri::An,
        }
    }
}

impl fmt::Display for BaTri {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.ten())
    }
}
