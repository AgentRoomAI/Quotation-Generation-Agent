from app import _add_products_from_message

parsed, items = _add_products_from_message('I need 10 laptops and 5 mobiles')
print('Parsed:', parsed)
print('Items:')
for prod, qty in items:
    print('-', prod.id, prod.name, 'qty=', qty)
print('Total items:', len(items))
