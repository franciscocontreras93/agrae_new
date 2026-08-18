"""Complete catalog for the experimental CNH all-fields Shapefile."""

from __future__ import annotations


def _field(source: str, status: str, meaning: str) -> dict[str, str]:
    return {"source": source, "status": status, "meaning": meaning}


ALL_FIELD_CATALOG = {
    "mfr": _field("constant", "verified", "manufacturer"),
    "src_file": _field("ZIP", "verified", "TLO member path"),
    "src_rec": _field("TLO", "verified", "zero-based record index"),
    "src_off": _field("TLO", "verified", "zero-based byte offset"),
    "rec_id": _field("all@11:u32le", "verified", "join identifier"),
    "pos_time": _field("TLO@27:6B", "verified", "position timestamp"),
    "harv_time": _field("TLH@27:6B", "verified", "harvest timestamp"),
    "flow_dly": _field("TLH time - TLO time", "verified", "delay seconds"),
    "hyp_lat": _field("TLO@39:i32le/1e7", "experimental", "latitude hypothesis"),
    "hyp_lon": _field("TLO@43:i32le/1e7", "experimental", "longitude hypothesis"),
    "elev_m": _field("TLO@47:i32le/1000", "candidate", "elevation metres"),
    "head_deg": _field("TLO@56:u16le/10", "candidate", "heading degrees"),
    "speed_ms": _field("TLT@35:u16le/100", "candidate", "speed metres per second"),
    "width_m": _field("TLT@39:u16le/100", "candidate", "working width metres"),
    "moist_pc": _field("TLH@38:u16le/10", "candidate", "harvest moisture percent"),
    "o_u33": _field("TLO@33:u16le", "unknown", "spatial channel 33"),
    "o_u35": _field("TLO@35:u16le", "unknown", "spatial channel 35"),
    "o_u37": _field("TLO@37:u16le", "unknown", "spatial channel 37"),
    "raw_a": _field("TLO@39:i32le", "candidate", "primary X/Y channel A"),
    "raw_b": _field("TLO@43:i32le", "candidate", "primary X/Y channel B"),
    "o_i47": _field("TLO@47:i32le", "candidate", "elevation raw"),
    "o_u51": _field("TLO@51:u32le", "unknown", "spatial channel 51"),
    "o_u55": _field("TLO@55:u8", "candidate", "signal or recording state"),
    "o_u56": _field("TLO@56:u16le", "candidate", "heading raw"),
    "o_a2": _field("TLO@58:i32le", "unknown", "secondary X/Y channel A"),
    "o_b2": _field("TLO@62:i32le", "unknown", "secondary X/Y channel B"),
    "o_a3": _field("TLO@66:i32le", "unknown", "tertiary X/Y channel A"),
    "o_b3": _field("TLO@70:i32le", "unknown", "tertiary X/Y channel B"),
    "has_t": _field("join", "verified", "TLT record present"),
    "t_u33": _field("TLT@33:u16le", "candidate", "satellite count"),
    "t_u35": _field("TLT@35:u16le", "candidate", "speed raw"),
    "t_u37": _field("TLT@37:u16le", "unknown", "constant zero in sample"),
    "t_u39": _field("TLT@39:u16le", "candidate", "working width raw"),
    "has_h": _field("join", "verified", "TLH record present"),
    "h_u33": _field("TLH@33:u8", "unknown", "constant one in sample"),
    "h_u34": _field("TLH@34:u16le", "unknown", "harvest channel A: mass/volume/flow/yield"),
    "h_u36": _field("TLH@36:u16le", "unknown", "harvest channel B: mass/volume/flow/yield"),
    "h_u38": _field("TLH@38:u16le", "candidate", "moisture raw"),
    "h_u40": _field("TLH@40:u16le", "unknown", "harvest channel 40"),
    "h_u42": _field("TLH@42:u16le", "unknown", "harvest channel 42"),
    "h_u44": _field("TLH@44:u16le", "unknown", "harvest channel 44"),
    "h_u46": _field("TLH@46:u16le", "unknown", "harvest channel 46"),
    "h_u48": _field("TLH@48:u16le", "unknown", "harvest channel 48"),
    "o_hex": _field("TLO@33:41B", "raw", "complete TLO payload hexadecimal"),
    "t_hex": _field("TLT@33:14B", "raw", "complete TLT payload hexadecimal"),
    "h_hex": _field("TLH@33:17B", "raw", "complete TLH payload hexadecimal"),
}
