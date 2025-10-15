import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  //creamos la url privada
  private apiUrl = 'http://localhost:8000/BoaNK/login';

  //hacemos el constructor
  constructor(private http: HttpClient) { }

  //creamos la funcion del login
  login(usuario: string, contraseña: string): Observable<any> {
    const body = { usuario, contraseña };
    return this.http.post(`${this.apiUrl}`, body);
  }
}
