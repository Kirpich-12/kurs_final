from .repo import DataRepo
from .parser import Parser



def main():
    data_repo = DataRepo()
    parser = Parser()

    bank_branches = parser.get_usd()

    for branch in bank_branches:
        data_repo.set_bank_branch(branch)


if __name__ == "__main__":
    main()