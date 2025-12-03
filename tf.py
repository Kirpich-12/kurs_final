class Obj:
    def __init__(self, age:int):
        self.age = age
    
    def __int__(self):
        return self.age * 2


obj = int(Obj(3))
print(obj)