import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { AuthStoreService } from '../auth/auth-store';

export interface CarritoInterface {
  id_carrito: string;
  id_usuario: string;
  id_detalle_carrito: string;
  id_platillo: string;
  Nombre_platillo: string;
  detalles_adicionales: string;
  precio_unitario: number;
  Ruta_imagen: string;

  detalle_adicional?: string;
  cantidad_plato?: number;
}

export interface TemporalInterface {
  datos_pedido?: any[];
  fecha_creacion?: Date;
  pagado?: boolean;
  precio?: number;
  lista_producto?: any[];
  metodo_pago?: string;
  id_tarjeta?: string;
  direccion?: string;
  id_mesa?: string;
}


export interface DireccionInterface {
  id_direccion?: string;
  alias: string;
  Calle: string;
  No_ext: string;
  No_int?: string;
  Colonia: string;
  CP: number;
  Ciudad?: string;
  Municipio: string;
  Estado: string;
  predeterminada?: false;
  instrucciones_add?: string;
}

export interface TarjetaInterface {
  id_tarjeta?: string;
  titular: string;
  num_tarjeta: string;
  id_tipo_tarjeta?: number;
  fecha_exp: string;
}


@Injectable({ providedIn: 'root' })
export class CarritoService {
  private apiUrlCarrito = 'http://127.0.0.1:8000/carrito';
  private apiUrltemproal = 'http://127.0.0.1:8000/carrito_temporal';

  private apiCP = 'http://127.0.0.1:8000/utils/buscar_cp?codigo='
  private apiUrlDireccion = 'http://127.0.0.1:8000/direcciones'
  private apiUrlTarjeta = 'http://127.0.0.1:8000/tarjetas'

  constructor(private http: HttpClient, private authStore: AuthStoreService) { }

  private getHeaders(): HttpHeaders | null {
    const token = this.authStore.getToken();
    return token ? new HttpHeaders({ Authorization: `Bearer ${token}` }) : null;
  }

  getCarritoByUser(): Observable<CarritoInterface[]> {
    const headers = this.getHeaders();
    if (!headers) return of([]);

    return this.http.get<{ platillos: CarritoInterface[] }>(
      `${this.apiUrlCarrito}/get_by_user`,
      { headers }
    ).pipe(
      catchError(err => {
        console.error('Error al obtener carrito:', err);
        return of({ platillos: [] });
      }),
      // Extraer solo el array
      map(res => res.platillos || [])
    );
  }

  add_Carrito_by_User(
    id_platillo: string,
    precio_unitario: number,
    detalles_adicionales: string
  ): Observable<CarritoInterface[]> {
    const headers = this.getHeaders();
    if (!headers) return of([]);

    // Cuerpo de la solicitud
    const body = {
      id_platillo,
      precio_unitario,
      detalles_adicionales
    };

    return this.http.post<{ platillos: CarritoInterface[] }>(
      `${this.apiUrlCarrito}/agregar`,
      body,
      { headers }
    ).pipe(
      catchError(err => {
        console.error('Error al agregar al carrito:', err);
        return of({ platillos: [] });
      }),
      map(res => res.platillos || [])
    );
  }


  eliminarPlatillo(id_detalle_carrito: string): Observable<any> {
    const headers = this.getHeaders();
    if (!headers) return of(null);

    return this.http.delete(`${this.apiUrlCarrito}/eliminar/${id_detalle_carrito}`, { headers })
      .pipe(catchError(err => { console.error(err); return of(null); }));
  }



  agregar_temporal(data: {
    idscarrito: string[];
    precio: number;
    lista_producto: { nombre: string; cant: number }[];
  }): Observable<any> {
    const headers = this.getHeaders();
    if (!headers) return of(null);

    // Crear el cuerpo del POST siguiendo la interfaz TemporalInterface
    const body: TemporalInterface = {
      datos_pedido: data.idscarrito,
      fecha_creacion: new Date(),
      pagado: false,
      precio: data.precio,
      lista_producto: data.lista_producto
    };

    return this.http.post<any>(
      `${this.apiUrltemproal}/guardar`,
      body,
      { headers }
    );
  }


  buscarPorCP(cp: string): Observable<any> {
    const url = `${this.apiCP}${cp}`;

    return this.http.get(url);
  }
  agregar_direccion(data: DireccionInterface): Observable<DireccionInterface> {
    const headers = this.getHeaders();
    if (!headers) return of({} as DireccionInterface);

    return this.http.post<DireccionInterface>(
      `${this.apiUrlDireccion}/create_direccion`,
      data, // 👈 no lo pongas en un array
      { headers }
    ).pipe(
      catchError(err => {
        console.error('Error al agregar dirección:', err);
        return of({} as DireccionInterface);
      })
    );
  }


  get_direcciones_by_user(): Observable<DireccionInterface[]> {
    const headers = this.getHeaders();
    if (!headers) return of([]);

    return this.http.get<DireccionInterface[]>(
      `${this.apiUrlDireccion}/get_all_direcciones`,
      { headers }
    ).pipe(
      catchError(err => {
        console.error('Error al obtener las direcciones:', err);
        return of([]);
      })
    );
  }


  agregar_tarjeta(data: TarjetaInterface): Observable<TarjetaInterface> {
    const headers = this.getHeaders();
    if (!headers) return of({} as TarjetaInterface);

    return this.http.post<TarjetaInterface>(
      `${this.apiUrlTarjeta}/create_tarjetas`,
      data, // 👈 no lo pongas en un array
      { headers }
    ).pipe(
      catchError(err => {
        console.error('Error al agregar dirección:', err);
        return of({} as TarjetaInterface);
      })
    );
  }

  get_tarjetas_by_user(): Observable<TarjetaInterface[]> {
    const headers = this.getHeaders();
    if (!headers) return of([]);

    return this.http.get<TarjetaInterface[]>(
      `${this.apiUrlTarjeta}/get_all_tarjetas`,
      { headers }
    ).pipe(
      catchError(err => {
        console.error('Error al obtener las direcciones:', err);
        return of([]);
      })
    );
  }

  // funcion que se usa para añadir el metodo de pago y direccion al pedido
  update_temporal(data: TemporalInterface): Observable<any> {
    const headers = this.getHeaders();
    if (!headers) return of(null);

    // ✅ Asegura que solo se envíen las propiedades que existen
    const body: TemporalInterface = {
      metodo_pago: data.metodo_pago,
      ...(data.id_tarjeta ? { id_tarjeta: data.id_tarjeta } : {}),
      direccion: data.direccion,
      ...(data.id_mesa ? { id_mesa: data.id_mesa } : {}),
    };

    return this.http.put<any>(
      `${this.apiUrltemproal}/update_resumen`,
      body,
      { headers }
    );
  }

  get_resumen_pedido(): Observable<TemporalInterface[]> {
    const headers = this.getHeaders();
    if (!headers) return of([]);

    return this.http.get<TemporalInterface[]>(
      `${this.apiUrltemproal}/get_resumen`,
      { headers }
    ).pipe(
      catchError(err => {
        console.error('Error al obtener el resumen:', err);
        return of([]);
      })
    );
  }
}
