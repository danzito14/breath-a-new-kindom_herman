import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Producto } from '../home/productosService';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class Filtros {
  constructor(private http: HttpClient) { }

  apiUrltexto = 'http://127.0.0.1:8000/platillo';
  apiUrlCombo = 'http://127.0.0.1:8000/combos';

  get_productos_by_name(texto: string): Observable<Producto[]> {
    return this.http.get<Producto[]>(`${this.apiUrltexto}/get_platillo?Nombre_platillo=${texto}`);
  }

  get_productos_by_categoria(id_tipo: number): Observable<Producto[]> {
    return this.http.get<Producto[]>(`${this.apiUrltexto}/get_platillo_by_tipo?id_tipo_platillo=${id_tipo}`);
  }

  get_productos_by_price(min_price: number, max_price: number): Observable<Producto[]> {
    return this.http.get<Producto[]>(`${this.apiUrltexto}/get_platillo_by_price?min_price=${min_price}&max_price=${max_price}`)
  }

  get_combos_by_price(min_price: number, max_price: number): Observable<Producto[]> {
    return this.http.get<Producto[]>(`${this.apiUrlCombo}/get_combo_by_price?min_price=${min_price}&max_price=${max_price}`)
  }

}
