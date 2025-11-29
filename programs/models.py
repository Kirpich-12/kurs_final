from enum import StrEnum
from dataclasses import dataclass


class Currency(StrEnum):
    USD = "usd"
    BYN = "byn"
    RUB = "rub"
    EUR = "eur"
    CNY = "cny"


@dataclass
class BankOrg:
    name: str

    def __str__(self):
        return self.name


@dataclass
class ExchangeRate:
    curr_from: Currency
    curr_to: Currency
    rate: float


@dataclass
class Coords:
    lon: float
    lat: float

    def __str__(self):
        return f"{self.lon} {self.lat}"


@dataclass
class BankBranch:
    bank_org: BankOrg
    address: str
    coords: Coords
    exchange_rates: list[ExchangeRate]

    @property
    def id(self) -> int:
        return hash(
            str(self.bank_org) +
            str(self.address) +
            str(self.coords)
        )
