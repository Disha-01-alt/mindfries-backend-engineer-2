"""Members, their devices, and their coaches — the enrollment registry.

A sample is only accepted for an enrolled member + registered device (the
ingest service checks this), so this store is the gatekeeper for provenance.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core.errors import NotFoundError


@dataclass(frozen=True)
class Device:
    device_id: str
    member_id: str
    source: str  # goqii_band | apple_health | health_connect | lab | manual
    kind: str    # band | phone | scale | glucometer | bp_cuff


@dataclass
class Member:
    member_id: str
    name: str
    chronological_age: float
    coach_id: str | None = None
    enrolled_at: float | None = None
    device_ids: list[str] = field(default_factory=list)


class MemberStore:
    def __init__(self) -> None:
        self._members: dict[str, Member] = {}
        self._devices: dict[str, Device] = {}

    def enroll(self, member: Member) -> Member:
        self._members[member.member_id] = member
        return member

    def register_device(self, device: Device) -> Device:
        if device.member_id not in self._members:
            raise NotFoundError(f"member {device.member_id} not enrolled")
        self._devices[device.device_id] = device
        m = self._members[device.member_id]
        if device.device_id not in m.device_ids:
            m.device_ids.append(device.device_id)
        return device

    def get_member(self, member_id: str) -> Member:
        try:
            return self._members[member_id]
        except KeyError:
            raise NotFoundError(f"member {member_id} not enrolled") from None

    def get_device(self, device_id: str) -> Device:
        try:
            return self._devices[device_id]
        except KeyError:
            raise NotFoundError(f"device {device_id} not registered") from None

    def is_enrolled(self, member_id: str) -> bool:
        return member_id in self._members

    def has_device(self, device_id: str) -> bool:
        return device_id in self._devices

    def members(self) -> list[Member]:
        return list(self._members.values())

    def assign_coach(self, member_id: str, coach_id: str) -> Member:
        m = self.get_member(member_id)
        m.coach_id = coach_id
        return m
