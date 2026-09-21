//! mac.rs — dia chi MAC 6 byte + tien ich.

use std::fmt;

#[derive(Clone, Copy, PartialEq, Eq, Hash)]
pub struct Mac(pub [u8; 6]);

impl Mac {
    pub const ROI: Mac = Mac([0, 0, 0, 0, 0, 0]); // rong / khong xac dinh
    pub const QUANG_BA: Mac = Mac([0xff; 6]); // broadcast: ff:ff:ff:ff:ff:ff

    /// 3 byte dau = OUI (ma hang san xuat).
    pub fn oui(&self) -> [u8; 3] {
        [self.0[0], self.0[1], self.0[2]]
    }

    /// Bit thu 2 cua byte dau = 1 → MAC ngau nhien / cuc bo (privacy MAC cua dien thoai).
    /// Dau hieu quan trong: may co the dang GIAU danh tinh that.
    pub fn la_cuc_bo(&self) -> bool {
        self.0[0] & 0b0000_0010 != 0
    }

    pub fn la_quang_ba(&self) -> bool {
        *self == Mac::QUANG_BA
    }
}

impl fmt::Display for Mac {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}",
            self.0[0], self.0[1], self.0[2], self.0[3], self.0[4], self.0[5]
        )
    }
}

impl fmt::Debug for Mac {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self)
    }
}
