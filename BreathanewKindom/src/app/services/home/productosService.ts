import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Producto {
  id_platillo: string;
  id_tipo_platillo: number;
  Nombre_platillo: string;
  Ruta_imagen: string;
  precio_produccion: number;
  precio_venta: number;
  Receta: string;
  estatus: boolean;
  Descripcion: string;
}

@Injectable({
  providedIn: 'root'
})
export class ProductosService {
  private apiUrl = 'http://localhost:8000/platillo/get_all_platillos';

  constructor(private http: HttpClient) { }

  get_all_Productos(): Observable<Producto[]> {
    return this.http.get<Producto[]>(this.apiUrl);
  }
}
