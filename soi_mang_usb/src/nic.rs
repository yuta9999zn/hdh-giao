//! nic.rs — LOP GOC: gui/nhan KHUNG ETHERNET THO.
//!
//! Day la ranh gioi giua "phan giao thuc thuan tuy" (arp/soi/chen — test duoc,
//! doc lap HDH) va "phan cham phan cung". Muon port sang GIAO that su chi can
//! hien thuc lai trait `Nic` bang driver NIC cua GIAO; toan bo logic ben tren
//! khong doi mot dong.
//!
//! Hien co 1 hien thuc: `NicLinux` (AF_PACKET) — chay duoi WSL/Kali cua ban,
//! noi ban da co quyen raw. Can CAP_NET_RAW (chay bang sudo).

use crate::mac::Mac;
use std::io;

/// Trait trung tam. Bat/gui mot khung Ethernet nguyen ven (ke ca header 14 byte).
pub trait Nic {
    /// Gui 1 khung tho ra day.
    fn gui(&self, khung: &[u8]) -> io::Result<()>;

    /// Cho 1 khung, toi da `han_ms` mili-giay. Ok(None) = het gio, chua co gi (→ AN).
    fn nhan(&self, han_ms: u32) -> io::Result<Option<Vec<u8>>>;

    /// MAC cua chinh card mang nay.
    fn mac(&self) -> Mac;

    /// IPv4 cua chinh may nay tren giao dien do (dạng 4 byte).
    fn ipv4(&self) -> [u8; 4];

    /// Mat na mang (netmask) — de tinh dai dia chi can quet.
    fn mat_na(&self) -> [u8; 4];
}

// ================= Hien thuc Linux (AF_PACKET) =================
#[cfg(target_os = "linux")]
mod linux {
    use super::*;
    use std::os::unix::io::RawFd;

    const AF_PACKET: libc::c_int = 17;
    const ETH_P_ALL: u16 = 0x0003;
    const SIOCGIFINDEX: libc::c_ulong = 0x8933;
    const SIOCGIFHWADDR: libc::c_ulong = 0x8927;
    const SIOCGIFADDR: libc::c_ulong = 0x8915;
    const SIOCGIFNETMASK: libc::c_ulong = 0x891b;

    // ifreq cua Linux: 16 byte ten + 24 byte union. Ta doc/ghi thu cong.
    #[repr(C)]
    struct IfReq {
        ten: [u8; 16],
        du_lieu: [u8; 24],
    }

    #[repr(C)]
    struct SockaddrLl {
        sll_family: u16,
        sll_protocol: u16, // big-endian
        sll_ifindex: i32,
        sll_hatype: u16,
        sll_pkttype: u8,
        sll_halen: u8,
        sll_addr: [u8; 8],
    }

    pub struct NicLinux {
        fd: RawFd,
        ifindex: i32,
        mac: Mac,
        ipv4: [u8; 4],
        mat_na: [u8; 4],
    }

    fn ifreq_moi(ten_gd: &str) -> IfReq {
        let mut r = IfReq { ten: [0; 16], du_lieu: [0; 24] };
        let b = ten_gd.as_bytes();
        let n = b.len().min(15);
        r.ten[..n].copy_from_slice(&b[..n]);
        r
    }

    impl NicLinux {
        /// Mo giao dien theo ten (vd "eth0", "wlan0").
        pub fn mo(ten_gd: &str) -> io::Result<NicLinux> {
            unsafe {
                let fd = libc::socket(
                    AF_PACKET,
                    libc::SOCK_RAW,
                    (ETH_P_ALL.to_be()) as libc::c_int,
                );
                if fd < 0 {
                    return Err(io::Error::last_os_error());
                }

                // ifindex
                let mut r = ifreq_moi(ten_gd);
                if libc::ioctl(fd, SIOCGIFINDEX, &mut r) < 0 {
                    let e = io::Error::last_os_error();
                    libc::close(fd);
                    return Err(e);
                }
                let ifindex = i32::from_ne_bytes([r.du_lieu[0], r.du_lieu[1], r.du_lieu[2], r.du_lieu[3]]);

                // MAC (SIOCGIFHWADDR): sockaddr.sa_data bat dau o offset 2 cua du_lieu
                let mut r = ifreq_moi(ten_gd);
                if libc::ioctl(fd, SIOCGIFHWADDR, &mut r) < 0 {
                    let e = io::Error::last_os_error();
                    libc::close(fd);
                    return Err(e);
                }
                let mut m = [0u8; 6];
                m.copy_from_slice(&r.du_lieu[2..8]);
                let mac = Mac(m);

                // IPv4 (SIOCGIFADDR): sockaddr_in.sin_addr o offset 4 cua du_lieu
                let mut r = ifreq_moi(ten_gd);
                let ipv4 = if libc::ioctl(fd, SIOCGIFADDR, &mut r) == 0 {
                    [r.du_lieu[4], r.du_lieu[5], r.du_lieu[6], r.du_lieu[7]]
                } else {
                    [0, 0, 0, 0]
                };

                // Netmask
                let mut r = ifreq_moi(ten_gd);
                let mat_na = if libc::ioctl(fd, SIOCGIFNETMASK, &mut r) == 0 {
                    [r.du_lieu[4], r.du_lieu[5], r.du_lieu[6], r.du_lieu[7]]
                } else {
                    [255, 255, 255, 0]
                };

                // Bind vao dung giao dien
                let sll = SockaddrLl {
                    sll_family: AF_PACKET as u16,
                    sll_protocol: ETH_P_ALL.to_be(),
                    sll_ifindex: ifindex,
                    sll_hatype: 0,
                    sll_pkttype: 0,
                    sll_halen: 0,
                    sll_addr: [0; 8],
                };
                let rc = libc::bind(
                    fd,
                    &sll as *const _ as *const libc::sockaddr,
                    std::mem::size_of::<SockaddrLl>() as libc::socklen_t,
                );
                if rc < 0 {
                    let e = io::Error::last_os_error();
                    libc::close(fd);
                    return Err(e);
                }

                Ok(NicLinux { fd, ifindex, mac, ipv4, mat_na })
            }
        }
    }

    impl Nic for NicLinux {
        fn gui(&self, khung: &[u8]) -> io::Result<()> {
            let sll = SockaddrLl {
                sll_family: AF_PACKET as u16,
                sll_protocol: ETH_P_ALL.to_be(),
                sll_ifindex: self.ifindex,
                sll_hatype: 0,
                sll_pkttype: 0,
                sll_halen: 6,
                sll_addr: [0; 8],
            };
            let n = unsafe {
                libc::sendto(
                    self.fd,
                    khung.as_ptr() as *const libc::c_void,
                    khung.len(),
                    0,
                    &sll as *const _ as *const libc::sockaddr,
                    std::mem::size_of::<SockaddrLl>() as libc::socklen_t,
                )
            };
            if n < 0 {
                return Err(io::Error::last_os_error());
            }
            Ok(())
        }

        fn nhan(&self, han_ms: u32) -> io::Result<Option<Vec<u8>>> {
            // poll de ton trong 'an' = het gio, khong treo mai.
            let mut pfd = libc::pollfd {
                fd: self.fd,
                events: libc::POLLIN,
                revents: 0,
            };
            let rc = unsafe { libc::poll(&mut pfd, 1, han_ms as libc::c_int) };
            if rc < 0 {
                return Err(io::Error::last_os_error());
            }
            if rc == 0 {
                return Ok(None); // → AN
            }
            let mut buf = vec![0u8; 2048];
            let n = unsafe {
                libc::recv(self.fd, buf.as_mut_ptr() as *mut libc::c_void, buf.len(), 0)
            };
            if n < 0 {
                return Err(io::Error::last_os_error());
            }
            buf.truncate(n as usize);
            Ok(Some(buf))
        }

        fn mac(&self) -> Mac {
            self.mac
        }
        fn ipv4(&self) -> [u8; 4] {
            self.ipv4
        }
        fn mat_na(&self) -> [u8; 4] {
            self.mat_na
        }
    }

    impl Drop for NicLinux {
        fn drop(&mut self) {
            unsafe {
                libc::close(self.fd);
            }
        }
    }
}

#[cfg(target_os = "linux")]
pub use linux::NicLinux;
