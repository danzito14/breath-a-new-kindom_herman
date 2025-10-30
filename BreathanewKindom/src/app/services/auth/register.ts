import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface InterfaceUsuario {
  id_nvl_usuario: number;
  Nickname: string;
  Contraseña?: string;
  Nombre: string;
  Apellido: string;
  Correo_electronico: string;
  estatus?: boolean;
  contrasena?: string; // viene desde el HTML
}

@Injectable({
  providedIn: 'root'
})
export class RegisterService {
  private apiUrl = 'http://localhost:8000/user/create_user';

  constructor(private http: HttpClient) { }

  registro(usuario: InterfaceUsuario): Observable<any> {
    // Crear una copia del objeto para no mutar el original
    const body = { ...usuario };

    // Asignar Contraseña con el valor recibido como contrasena
    body.Contraseña = body.contrasena;
    delete body.contrasena; // eliminar la propiedad que no necesita el backend

    // Asignar valor por defecto a estatus si no viene del HTML
    body.estatus = false;

    return this.http.post(this.apiUrl, body);
  }
}
