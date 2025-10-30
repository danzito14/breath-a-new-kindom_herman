import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface Categoria {
  id_tipo_platillo: number;
  descripcion: string;
  estatus: boolean;
  ruta_icono: string;
}

@Injectable({
  providedIn: 'root'
})
export class CategoriasService {
  private apiUrl = 'http://127.0.0.1:8000/tipo_platillos/get_all_tipo_platillos';

  constructor(private http: HttpClient) { }

  get_all_categorias(): Observable<Categoria[]> {
    return this.http.get<Categoria[]>(this.apiUrl);
  }
}
