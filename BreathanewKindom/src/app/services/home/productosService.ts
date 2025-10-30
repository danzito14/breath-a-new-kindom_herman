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

  opciones?: OpcionesPlatillo[];
  precio_final?: any;
  detalle_adicional?: string;

  // para indicar si tiene oferta 
  En_oferta?: boolean;
  Porcentaje_oferta?: string;
  precio_original?: string;
  color?: string;
  descripcion?: string;
}

export interface CombosInterface {
  id_combo: string;
  Nombre_combo: string;
  Descripcion: string;
  Ruta_imagen: string;
  precio_combo: number;
  estatus: boolean;
}

export interface tipo_platilloInterface {
  id_tipo_platillo: number;
  descripcion: string;
  estatus: string;
  ruta_icono: string;
  color: string
}

export interface ProductoConFavorito extends Producto {
  isFavorite: boolean;
  id_favorito: string | null;
}

export interface OpcionesPlatillo {
  id_option: number;
  id_platillo: string;
  opcion: string;
  precio: number
}

export interface idsCombo {
  id_platillo: string;
}

@Injectable({
  providedIn: 'root'
})
export class ProductosService {
  private apiUrl = 'http://localhost:8000/platillo/get_all_platillos';
  private apiUrlCombos = 'http://127.0.0.1:8000/combos/get_combo_cabeza';
  private apiUrlidsCombos = 'http://127.0.0.1:8000/combos/id_platos?id_combo=';
  private apiUrltipoplatillo = 'http://127.0.0.1:8000/tipo_platillos/get_all_tipo_platillos';
  private apiUrlid = 'http://127.0.0.1:8000/platillo/get_platillo_id?id=';
  private apiUrlopcion = 'http://127.0.0.1:8000/platillos/get_platillo_option?id_platillo=';
  constructor(private http: HttpClient) { }

  get_all_Productos(): Observable<Producto[]> {
    return this.http.get<Producto[]>(this.apiUrl);
  }

  get_all_combos(): Observable<CombosInterface[]> {
    return this.http.get<CombosInterface[]>(this.apiUrlCombos);
  }

  get_tipo_paltillo(): Observable<tipo_platilloInterface[]> {
    return this.http.get<tipo_platilloInterface[]>(this.apiUrltipoplatillo);
  }

  get_platillo_id(id_producto: string): Observable<Producto[]> {
    return this.http.get<Producto[]>(`${this.apiUrlid}${id_producto}`)
  }

  get_opciones_platillo(id_producto: string): Observable<OpcionesPlatillo[]> {
    return this.http.get<OpcionesPlatillo[]>(`${this.apiUrlopcion}${id_producto}`)
  }

  get_ids_combo(id_combo: string): Observable<idsCombo[]> {
    return this.http.get<idsCombo[]>(`${this.apiUrlidsCombos}${id_combo}`)
  }

}
