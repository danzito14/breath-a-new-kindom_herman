import { Component, Input, Output, EventEmitter, ChangeDetectorRef, NgZone } from '@angular/core';
import { CarritoInterface, CarritoService } from '../../services/carrito/carrito';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-tarjeta-carrito',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tarjeta-carrito.html',
  styleUrls: ['./tarjeta-carrito.css']
})
export class TarjetaCarrito {
  @Input() platillosCarrito: CarritoInterface[] = [];
  @Input() cargar: String = "";
  @Input() boton_eliminar = true;
  @Input() checkbox: boolean = true;
  @Output() eliminar = new EventEmitter<string>();


  // 🔹 Nuevo: emitimos los seleccionados
  @Output() seleccionCambiada = new EventEmitter<CarritoInterface[]>();
  seleccionados: Set<string> = new Set(); // guardamos los id seleccionados


  constructor(private carritoService: CarritoService,
    private zone: NgZone, private cd: ChangeDetectorRef
  ) { }


  ngOnInit() {
    if (this.cargar === "carrito") {
      this.cargarPlatillos();
    } else if (this.cargar === "pedido") {

    }
  }

  cargarPlatillos() {
    this.carritoService.getCarritoByUser().subscribe(platillos => {
      this.zone.run(() => {

        this.platillosCarrito = platillos;
        this.cd.detectChanges();  // 🔹 Forzar actualización
      });
    });

  }

  eliminarPlatillo(id_detalle_carrito: string) {
    this.carritoService.eliminarPlatillo(id_detalle_carrito).subscribe({
      next: (res) => {
        // 🔹 Quitar el producto del arreglo del carrito
        this.platillosCarrito = this.platillosCarrito.filter(
          p => p.id_detalle_carrito !== id_detalle_carrito
        );

        // 🔹 Si estaba seleccionado, eliminarlo también del set de seleccionados
        if (this.seleccionados.has(id_detalle_carrito)) {
          this.seleccionados.delete(id_detalle_carrito);
          // 🔹 Emitir la nueva selección al padre
          const seleccion = this.platillosCarrito.filter(p => this.seleccionados.has(p.id_detalle_carrito));
          this.seleccionCambiada.emit(seleccion);
        }

        // 🔹 Forzar actualización del DOM
        this.cd.detectChanges();

        console.log(`Platillo ${id_detalle_carrito} eliminado del carrito`);
      },
      error: (err) => {
        console.error('Error al eliminar platillo del carrito:', err);
      }
    });
  }


  cargarplatillosPedido() {

  }



  // 🔹 Nuevo: cuando se cambia un checkbox
  toggleSeleccion(platillo: CarritoInterface, event: Event) {
    const checked = (event.target as HTMLInputElement).checked;

    if (checked) {
      this.seleccionados.add(platillo.id_detalle_carrito);
    } else {
      this.seleccionados.delete(platillo.id_detalle_carrito);
    }

    // Emitimos los productos seleccionados completos, no solo los IDs
    const seleccion = this.platillosCarrito.filter(p => this.seleccionados.has(p.id_detalle_carrito));
    this.seleccionCambiada.emit(seleccion);
  }

}
