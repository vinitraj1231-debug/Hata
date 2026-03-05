"""
╔══════════════════════════════════════════╗
║        MODELS — Track dataclass          ║
╚══════════════════════════════════════════╝
"""
from dataclasses import dataclass


@dataclass
class Track:
    id:           str
    title:        str
    filepath:     str
    duration:     int
    url:          str
    requested_by: str
    thumbnail:    str = ""
