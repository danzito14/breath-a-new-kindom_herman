import { ChangeDetectorRef, Component, NgZone, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CarritoService, DireccionInterface, TarjetaInterface, TemporalInterface } from '../../services/carrito/carrito';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-direccion-pago',
  imports: [CommonModule, FormsModule],
  templateUrl: './direccion-pago.html',
  styleUrls: ['../../app.css', './direccion-pago.css']
})
export class DireccionPago implements OnInit {
  direcciones: DireccionInterface[] = [];
  tarjetas: TarjetaInterface[] = [];
  direccionSeleccionada: string | null = null;

  tarjetaSeleccionada: string | null = null; // ✅ nombre correcto
  metodoPagoSeleccionado: any;
  constructor(
    private router: Router,
    private carritoService: CarritoService,
    private zone: NgZone,
    private cd: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.obtener_direccions();
    this.obtener_tarjetas(); // ✅ ahora sí se obtienen las tarjetas
  }

  agregar_tarjeta_o_direccion(agregar: string) {
    this.router.navigate(['/general'], { queryParams: { agregar, accion: 'agregar' } });
  }

  obtener_direccions() {
    this.carritoService.get_direcciones_by_user().subscribe(direcciones => {
      this.zone.run(() => {
        this.direcciones = direcciones;
        this.cd.detectChanges();
      });
    });
  }

  obtener_tarjetas() {
    this.carritoService.get_tarjetas_by_user().subscribe(tarjet => {
      this.zone.run(() => {
        this.tarjetas = tarjet;
        this.cd.detectChanges();
      });
    });
  }
  guardar_direccion_pago() {
    if (!this.direccionSeleccionada || !this.metodoPagoSeleccionado) {
      alert("Seleccione un método de pago y una dirección para el pedido");
      return;
    }

    const metodopago = this.metodoPagoSeleccionado === 'Efectivo' ? 'Efectivo' : 'Tarjeta';
    const direccion = this.direcciones.find(d => d.id_direccion === this.direccionSeleccionada);
    const direccion_elegida = `${direccion?.Calle}, ${direccion?.No_ext}, ${direccion?.No_int}, ${direccion?.Colonia}, ${direccion?.CP}, ${direccion?.Ciudad}, ${direccion?.Estado}`;

    // 🔹 Declara el body fuera del if/else
    let body: TemporalInterface = {
      metodo_pago: metodopago,
      direccion: direccion_elegida
    };

    // 🔹 Si el método de pago es tarjeta, añade el id_tarjeta
    if (this.metodoPagoSeleccionado !== 'Efectivo') {
      body.id_tarjeta = this.metodoPagoSeleccionado!;
    }

    // 🔹 Enviar al servicio
    this.carritoService.update_temporal(body).subscribe({
      next: (res) => {
        console.log('Carrito temporal guardado:', res);
        this.router.navigate(['/resumen-pedido']);

      },
      error: (err) => {
        console.error('Error al guardar el carrito temporal:', err);
      }
    });
  }

}
