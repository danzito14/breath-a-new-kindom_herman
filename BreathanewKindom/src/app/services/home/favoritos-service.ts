import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { Producto } from './productosService';

export interface FavoritoInterface extends Producto {
  id_favorito: string;
  id_usuario: string;
  id_platillo: string;
  Platillo: string;
  Ruta_imagen: string;
  fecha_creacion?: string; // opcional si tu backend la devuelve
}

@Injectable({
  providedIn: 'root'
})
export class FavoritosService {

  private apiUrl = 'http://127.0.0.1:8000/favoritos';

  constructor(private http: HttpClient) { }

  // 🔹 Obtener token de forma segura
  private getToken(): string {
    if (typeof window === 'undefined') {
      return ''; // No hay localStorage (SSR), retornamos vacío
    }
    localStorage.getItem('token') // Debe devolver tu JWT
    console.log("aaaaaaa");
    return localStorage.getItem('token') || '';
  }

  // 🔹 Obtener favoritos del usuario
  get_favoritos_user(): Observable<FavoritoInterface[]> {
    const token = this.getToken();
    if (!token) {
      console.log("no token")
      return of([]); // No hay token, devolvemos arreglo vacío
    }

    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });
    return this.http.get<FavoritoInterface[]>(`${this.apiUrl}/get_all_favoritos/${token}`, { headers });
  }

  // 🔹 Agregar un platillo a favoritos
  agregarFavorito(id_platillo: string): Observable<FavoritoInterface> {
    const token = this.getToken();
    if (!token) {
      return of(null as any);
    }

    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });

    // Fecha actual en formato ISO
    const fecha_actual = new Date().toISOString().split('T')[0];


    const body = {
      id_platillo,
      id_usuario: token,
      fecha_agregado: fecha_actual
    };

    return this.http.post<FavoritoInterface>(
      `${this.apiUrl}/create_favorito`,
      body,
      { headers }
    );
  }

  // 🔹 Eliminar favorito
  eliminarFavorito(id_favorito: string): Observable<any> {
    const token = this.getToken();
    if (!token) {
      return of(null);
    }

    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });
    return this.http.delete(`${this.apiUrl}/delete_favorito/${id_favorito}`, { headers });
  }
}
