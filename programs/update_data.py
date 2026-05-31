from repo import DataRepo
from parser import Parser
from models import Link

USD = Link.USD
EUR = Link.EUR
CNY = Link.CNY
CHF = Link.CHF #швейцарский франк
# возможности расширить список валют(опционально парсинг)


def get_data(src: Link):
        print(f"[DEBUG] get_data() called with src={src}")
        data_repo = DataRepo()
        parser = Parser(True)
    
        print("[DEBUG] Calling parser.get_branch()...")
        bank_branches = parser.get_branch(src)
        print(f"[DEBUG] Parser returned {len(bank_branches) if bank_branches else 0} branches")
        
        if bank_branches:
            for i, branch in enumerate(bank_branches):
                print(f"[DEBUG] Saving branch {i}: {branch.bank_org.name}")
                data_repo.set_bank_branch(branch)
            print(f"[DEBUG] Saved {len(bank_branches)} branches to DB")
        
        return bank_branches


def main():
    get_data(Link.USD)
    #get_data(Link.EUR)
    #get_data(Link.CNY)
    #get_data(Link.CHF)

if __name__ == "__main__":
    main()