from fastapi import FastAPI
from pydantic import BaseModel
from enum import Enum
from typing import Union
app = FastAPI()

class proveedor(Enum):
    barcel = 'barcel'
    bimbo = 'bimbo'
    Coca = 'Coca'

class Item(BaseModel):
    name: str
    precio: int
    in_stock: bool
    proveedor: proveedor

items = [
    {
        'name': 'Takis',
        'precio': 20,
        'in_stock': True,
        'proveedor': 'barcel'
    },
    {

        'name': 'Donitas bimbo',
        'precio': 25,
        'in_stock': True,
        'proveedor': 'bimbo'
    },
    {

        'name': 'Coca',
        'precio': 21,
        'in_stock': True,
        'proveedor': 'Coca'
    }
]

products_list = [
    {
        'id': 1,
        'name' : 'martillo',
        'in_stock': True
    },
    {
        'id': 2,
        'name': 'clavo',
        'in_stock': True
    },

    {
        'id': 3,
        'name': 'tuerca',
        'in_stock': True
    },

    {
        'id': 4,
        'name': 'llave',
        'in_stock': True
    }
]

# el get recibe para obtener datos
@app.get('/')
def index():
    return  {
        'message':'Now it is Danzito time'
    }

@app.get('/item')
def get_items():
    return {
        'productos': items
    }

@app.get('/item/{item_name}')
def get_item(item_name: str):
    print(item_name)
    for item in items:
        if item['name'] == item_name:
            return {'item': item}
    return {'error':'Producto no encontrado'}

@app.post('/item')
def create_item(item_data: Item):
    print(item_data)
    items.append(item_data)
    return {
        'new_item': item_data
    }

@app.put('/items/{item_name}')
def uptade_item(item_name: str, item_data: Item):
    for item in items:
        if item['name'] == item_name:
            item['name'] = item_data.name
            item['precio'] = item_data.precio
            item['in_stock'] = item_data.in_stock
            item['proveedor'] = item_data.proveedor
            return{
                'item_ipdate': item
            }
    return {
        'error':'Producto no encontrado'
    }

@app.delete('/items/{item_name}')
def delete_item(item_name: str):
    for item in items:
        if item['name'] == item_name:
            items.remove(item)
            return {
                'item_remove': item_name + 'ha sido eliminado'
            }
        return {
            'error': 'item no encontrado'
        }

@app.get('/products')
def get_products(product_id: Union[int, None] = None):
    if product_id is None:
        return {
            'product': products_list
        }
    for product in products_list:
        if product['id'] == product_id:
            return {
                'product': product
            }
    return{
        'status' : 404,
        'error' : 'errrrrgg esta mal en algo'
    }
@app.get('/products1')
def get_products(product_id: str):
    for product in products_list:
        if product['id'] == product_id:
            return {
                'product': product
            }
    return{
        'status' : 404,
        'error' : 'errrrrgg esta mal en algo'
    }
