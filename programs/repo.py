import os
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Предполагается, что эти модели у вас уже описаны в models.py
from models import (
    Currency,
    Coords,
    BankOrg,
    BankBranch,
    ExchangeRate
)

# Базовый класс для моделей SQLAlchemy
Base = declarative_base()

# --- ORM Модели БД ---

class DBBankBranch(Base):
    """Модель таблицы отделений банка"""
    __tablename__ = 'bank_branches'

    id = Column(Integer, primary_key=True)
    bank_org = Column(String, nullable=False)
    address = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)

    # Связь с курсами валют. cascade="all, delete-orphan" автоматически удалит курсы при удалении отделения
    rates = relationship("DBExchangeRate", back_populates="branch", cascade="all, delete-orphan")


class DBExchangeRate(Base):
    """Модель таблицы курсов валют"""
    __tablename__ = 'exchange_rates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_id = Column(Integer, ForeignKey('bank_branches.id'), nullable=False)
    curr_from = Column(String, nullable=False)
    curr_to = Column(String, nullable=False)
    rate = Column(Float, nullable=False)

    branch = relationship("DBBankBranch", back_populates="rates")


# --- Основной репозиторий ---

class DataRepo:
    def __init__(self, db_name: str = "branch.db"):
        self.db_name = db_name
        self.db_url = f"sqlite:///{self.db_name}"
        
        # Инициализируем БД
        self._init_db()
        
        # Создаем фабрику сессий
        self.Session = sessionmaker(bind=self.engine)

    def _init_db(self):
        """Проверяет существование БД и создает таблицы, если их нет."""
        self.engine = create_engine(self.db_url, echo=False)
        # SQLAlchemy сама проверяет наличие таблиц. Если файла нет - он будет создан.
        Base.metadata.create_all(self.engine)

    def _to_domain_model(self, db_branch: DBBankBranch) -> BankBranch:
        """Вспомогательная функция для конвертации ORM-модели в доменную модель (BankBranch)"""
        exchange_rates = [
            ExchangeRate(
                curr_from=Currency(r.curr_from),
                curr_to=Currency(r.curr_to),
                rate=r.rate
            )
            for r in db_branch.rates
        ]

        return BankBranch(
            bank_org=BankOrg(name=db_branch.bank_org),
            address=db_branch.address,
            coords=Coords(lon=db_branch.lon, lat=db_branch.lat),
            exchange_rates=exchange_rates
        )

    # --- C: Create ---
    def set_bank_branch(self, bank_branch: BankBranch) -> BankBranch:
        """Сохранение или обновление отделения в БД"""
        with self.Session() as session:
            # Проверяем, есть ли уже такое отделение (по адресу и имени банка)
            bank_name = bank_branch.bank_org.name if hasattr(bank_branch.bank_org, 'name') else str(bank_branch.bank_org)
            existing = session.query(DBBankBranch).filter_by(
                bank_org=bank_name,
                address=bank_branch.address
            ).first()

            if existing:
                # Если есть, обновляем курсы
                existing.lat = bank_branch.coords.lat
                existing.lon = bank_branch.coords.lon
                
                # Удаляем старые курсы
                for old_rate in existing.rates:
                    session.delete(old_rate)
                
                # Добавляем новые
                for r in bank_branch.exchange_rates:
                    new_rate = DBExchangeRate(
                        curr_from=r.curr_from.value,
                        curr_to=r.curr_to.value,
                        rate=r.rate
                    )
                    existing.rates.append(new_rate)
                
                session.commit()
                return bank_branch

            # Создаем новую запись
            new_branch = DBBankBranch(
                bank_org=bank_name,
                address=bank_branch.address,
                lat=bank_branch.coords.lat,
                lon=bank_branch.coords.lon
            )

            # Добавляем курсы
            for r in bank_branch.exchange_rates:
                new_rate = DBExchangeRate(
                    curr_from=r.curr_from.value,
                    curr_to=r.curr_to.value,
                    rate=r.rate
                )
                new_branch.rates.append(new_rate)

            session.add(new_branch)
            session.commit()
            
        return bank_branch

    # --- R: Read ---
    def get_bank_branch(self, id: int) -> BankBranch | None:
        """Получить BankBranch по id, вернет None если не найдено"""
        with self.Session() as session:
            db_branch = session.query(DBBankBranch).filter_by(id=id).first()
            if not db_branch:
                return None
            return self._to_domain_model(db_branch)

    def list_bank_branches(
        self,
        curr_from: Currency | None = None,
        curr_to: Currency | None = None
    ) -> list[BankBranch]:
        """Возвращает список подходящих отделений, отфильтрованных по курсу (SQL-запросом)"""
        with self.Session() as session:
            query = session.query(DBBankBranch)

            # Фильтрация прямо на уровне SQL базы данных (работает быстрее, чем в Python)
            if curr_from:
                query = query.filter(DBBankBranch.rates.any(curr_from=curr_from.value))
            
            if curr_to:
                query = query.filter(DBBankBranch.rates.any(curr_to=curr_to.value))

            db_branches = query.all()
            return [self._to_domain_model(b) for b in db_branches]

    # --- U: Update ---
    def update_bank_branche_rates(
        self,
        id: int,
        rates: list[ExchangeRate]
    ) -> BankBranch:
        """Обновляет курсы отделения. Выбрасывает ValueError, если не найдено."""
        with self.Session() as session:
            db_branch = session.query(DBBankBranch).filter_by(id=id).first()
            if not db_branch:
                raise ValueError(f"BankBranch with id={id} not found")

            # Удаляем старые курсы
            for old_rate in db_branch.rates:
                session.delete(old_rate)
            
            # Добавляем новые
            db_branch.rates = [
                DBExchangeRate(
                    curr_from=r.curr_from.value,
                    curr_to=r.curr_to.value,
                    rate=r.rate
                )
                for r in rates
            ]

            session.commit()
            
            # Обновляем объект из БД и возвращаем
            session.refresh(db_branch)
            return self._to_domain_model(db_branch)

    # --- D: Delete ---
    def delete_bank_branch(self, id: int) -> bool:
        """Удаляет отделение банка и все его курсы из БД"""
        with self.Session() as session:
            db_branch = session.query(DBBankBranch).filter_by(id=id).first()
            if not db_branch:
                return False  # или можно raise ValueError

            session.delete(db_branch)
            session.commit()
            return True


    # --- Data Export (для приложений, работающих с DataFrame) ---
    def get_branches_as_dataframe(self):
        """Экспортирует все отделения в pandas DataFrame для работы с картами и аналитикой"""
        import pandas as pd
        
        branches = self.list_bank_branches()
        print(f"[DEBUG] Total branches in DB: {len(branches)}")
        
        if not branches:
            return pd.DataFrame()
        
        data = []
        for i, branch in enumerate(branches):
            print(f"[DEBUG] Branch {i}: {branch.bank_org.name}, rates: {len(branch.exchange_rates)}")
            for r in branch.exchange_rates:
                print(f"  - {r.curr_from.value} -> {r.curr_to.value} = {r.rate}")
            
            usd_rate = next((r.rate for r in branch.exchange_rates 
                           if r.curr_from.value == 'usd' and r.curr_to.value == 'byn'), None)
            
            print(f"  USD->BYN rate: {usd_rate}")
            
            if usd_rate:
                bank_name = branch.bank_org.name if hasattr(branch.bank_org, 'name') else str(branch.bank_org)
                data.append({
                    'address': branch.address,
                    'bank_name': bank_name,
                    'buy_course': usd_rate,
                    'sell_course': next((r.rate for r in branch.exchange_rates 
                                       if r.curr_from.value == 'byn' and r.curr_to.value == 'usd'), 
                                       usd_rate),
                    'lat': branch.coords.lat,
                    'lon': branch.coords.lon
                })
        
        df = pd.DataFrame(data)
        print(f"[DEBUG] Exported {len(df)} rows to DataFrame")
        return df


def main():
    repo = DataRepo(db_name="branch.db")
    
    # Пример вызова
    ans = repo.list_bank_branches()
    for i in ans:
        print(i)

if __name__ == '__main__':
    main()