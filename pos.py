items = []

class Item:
    def __init__(self, name, price):
        self.index = len(items)
        self.name = name
        self.price = price
        self.quantity = 0
        items.append(self)

class PosTransaction:
    def __init__(self):
        self.items = []

    def add(self, item, quantity):
        item.quantity = quantity
        self.items.append(item)

    def display(self):
        for item in self.items:
            print(str(item.price * item.quantity) + "\t(" +
                  str(item.quantity) + " x " + str(item.price)  + ")  ----  " + item.name)

    @property
    def total(self):
        t = 0
        for item in self.items:
            t += item.price * item.quantity
        return t


def display_inventory():
    for item in items:
        print(str(item.index) + "  ----  php" + str(item.price) +
              "  ----  " + item.name)

i1 = Item("coffee", 20)
i2 = Item("noodles", 22)
i3 = Item("milk tea", 30)
i4 = Item("softdrink 12oz", 18)
i5 = Item("softdrink 8oz", 12)
