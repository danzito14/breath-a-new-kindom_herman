import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Oferta_home {
  id_oferta_platillo: string;
  id_oferta: string;
  id_platillo: string;
  Nombre_platillo: string;
  Ruta_imagen: string;
  precio_venta: number;
  porcentaje_descuento: number;
  precio_oferta: number;
  Descripcion: string;
}


export interface ProductoConFavorito extends Oferta_home {
  isFavorite: boolean;
  id_favorito: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class OfertasService {
  private apiUrl = 'http://127.0.0.1:8000/ofertas/get_ofertas_for_home';

  constructor(private http: HttpClient) { }

  get_all_product_for_home(): Observable<Oferta_home[]> {
    return this.http.get<Oferta_home[]>(this.apiUrl);
  }
}


