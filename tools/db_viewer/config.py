from dataclasses import dataclass


@dataclass
class DbConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
