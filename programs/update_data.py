from repo import DataRepo
from parser import Parser

USD = 'https://myfin.by/currency/usd'


def main():
    data_repo = DataRepo()
    parser = Parser(True)

    bank_branches = parser.get_branch(USD)

    for branch in bank_branches:
        data_repo.set_bank_branch(branch)


if __name__ == "__main__":
    main()