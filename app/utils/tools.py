def get_units(money, price):
    units_str = str(money / price)
    units_add_str = str((money + 1)  / price)
    break_point = 0
    for i in range(len(units_str)):
        break_point = i
        if units_str[i] != units_add_str[i]:
            break

    return float(units_add_str[:break_point + 1])