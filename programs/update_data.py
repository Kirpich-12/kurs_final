from repo import DataRepo
from parser import Parser
from models import Link

USD = Link.USD
EUR = Link.EUR
CNY = Link.CNY
CHF = Link.CHF #швейцарский франк
# возможности расширить список валют(опционально парсинг)


def get_data(src: Link):
        data_repo = DataRepo()
        parser = Parser(True)
    
        bank_branches = parser.get_branch(src)
    
        for branch in bank_branches:
            data_repo.set_bank_branch(branch)
        
        return bank_branches


def main():
    get_data(Link.USD)
    #get_data(Link.EUR)
    #get_data(Link.CNY)
    #get_data(Link.CHF)

if __name__ == "__main__":
    main()