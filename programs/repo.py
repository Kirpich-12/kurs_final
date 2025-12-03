
from models import (
    Currency,
    Coords,
    BankOrg,
    BankBranch,
    ExchangeRate
)


# CRUD - Create Update Read Delete

class DataRepo:

    def __init__(self):
        pass

    # хз как с фалами разобраться 
    def set_bank_branch(
            self,
            brank_branch: BankBranch
    ):
        ...

    #фильтр 
    def list_bank_branches(
            self,
            curr_from: Currency | None = None,
            curr_to: Currency | None = None
    ) -> list[BankBranch]:
        ...

    #замена
    def update_bank_branche_rates(
            self,
            id: int,
            rates: list[ExchangeRate]
    ) -> BankBranch:
        ...

    
    def delete_bank_branch(
            self,
            id: int
    ):
        
        ...
