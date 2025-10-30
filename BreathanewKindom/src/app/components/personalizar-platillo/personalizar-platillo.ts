import { CommonModule } from '@angular/common';
import { Component, Input, OnChanges, OnDestroy, SimpleChanges, ChangeDetectorRef } from '@angular/core';
import { BehaviorSubject, Observable, Subject, takeUntil } from 'rxjs';
import { ProductosService, Producto, OpcionesPlatillo } from '../../services/home/productosService';
import { CarritoService } from '../../services/carrito/carrito';
import { Router } from '@angular/router';


@Component({
  selector: 'app-personalizar-platillo',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './personalizar-platillo.html',
  styleUrls: ['./personalizar-platillo.css']
})
export class PersonalizarPlatillo implements OnChanges, OnDestroy {

  @Input() idsProductos: string[] | null = null;
  @Input() carrito: boolean = false;

  private resultadoSubject = new BehaviorSubject<Producto[]>([]);
  resultados$: Observable<Producto[]> = this.resultadoSubject.asObservable();
  private destroy$ = new Subject<void>();

  constructor(private productoService: ProductosService, private cd: ChangeDetectorRef,
    private carritoservice: CarritoService, private router: Router  // 🔹 agregado
  ) { }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['idsProductos'] && this.idsProductos?.length) {
      this.buscar_productos(this.idsProductos);
    }
  }

  buscar_productos(ids: string[]) {
    // Limpiamos el Subject antes de buscar
    this.resultadoSubject.next([]);

    const productosCargados: Producto[] = [];

    ids.forEach(id => {
      this.productoService.get_platillo_id(id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (productos) => {
            if (productos.length) {
              const producto = productos[0];

              // Cargar opciones de cada producto
              this.productoService.get_opciones_platillo(producto.id_platillo)
                .pipe(takeUntil(this.destroy$))
                .subscribe({
                  next: (opciones: OpcionesPlatillo[]) => {
                    producto.opciones = opciones;
                    productosCargados.push(producto);
                    this.resultadoSubject.next([...productosCargados]);
                    this.cd.detectChanges(); // 🔹 fuerza actualización de la vista
                  },
                  error: (err) => console.error('Error cargando opciones', err)
                });
            }
          },
          error: (err) => console.error('Error cargando platillo', id, err)
        });
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  actualizarPrecio(producto: any, opcion: any, event: any) {
    // Si no tiene precio_final aún, inicialízalo con el precio base
    if (!producto.precio_final) {
      producto.precio_final = producto.precio_venta;
    }
    if (producto.detalle_adicional === undefined) {
      producto.detalle_adicional = "";
    }
    const checked = event.target.checked;

    if (checked) {
      // Si se marca el checkbox, suma el precio
      producto.precio_final += opcion.precio;
      producto.detalle_adicional += opcion.opcion + ", ";
      console.log(producto.precio_final);
      console.log(producto.detalle_adicional);
    } else {
      // Si se desmarca, resta el precio
      producto.precio_final -= opcion.precio;
      console.log(producto.precio_final);
    }
    console.log("algo no se")
  }


  agregar_carrito(id_platillo: string, precio_final: number, detalles_adicionales: string) {
    this.carritoservice.add_Carrito_by_User(id_platillo, precio_final, detalles_adicionales)
      .subscribe({
        next: (data) => {
          console.log('Carrito actualizado:', data);

          // 🔹 Eliminar producto del listado
          const productosActuales = this.resultadoSubject.value.filter(p => p.id_platillo !== id_platillo);
          this.resultadoSubject.next([...productosActuales]);
          this.cd.detectChanges();

          // 🔹 Si no quedan productos, redirigir a carrito
          if (productosActuales.length === 0) {
            this.router.navigate(['/carrito']);
          }
        },
        error: (err) => console.error(err)
      });
  }




}
