import { Component, OnInit } from '@angular/core';
import { CarritoInterface, CarritoService } from '../../services/carrito/carrito';
import { TarjetaCarrito } from '../../components/tarjeta-carrito/tarjeta-carrito';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-carrito',
  standalone: true,
  imports: [TarjetaCarrito, CommonModule],
  templateUrl: './carrito.html',
  styleUrls: ['./carrito.css']
})
export class Carrito implements OnInit {

  platillos: CarritoInterface[] = [];
  productosSeleccionados: CarritoInterface[] = [];
  total: number = 0;
  cargar: string = "carrito";

  // Lista con cantidad por id_platillo
  resumenSeleccion: { platillo: CarritoInterface, cantidad: number }[] = [];

  // Array con los IDs de detalle de carrito seleccionados
  public idscarrito: string[] = [];

  constructor(
    private carritoService: CarritoService,
    private router: Router
  ) { }

  ngOnInit() {
    this.cargarPlatillos();
  }

  cargarPlatillos() {
    this.carritoService.getCarritoByUser().subscribe(platillos => {
      this.platillos = platillos;
    });
  }

  // Se ejecuta cada vez que el hijo emite la selección
  onSeleccionChange(seleccion: CarritoInterface[]) {
    this.productosSeleccionados = seleccion;

    this.idscarrito = this.productosSeleccionados.map(p => p.id_detalle_carrito);

    // 🔹 Agrupar por id_platillo y contar cantidad
    const resumenMap = new Map<string, { platillo: CarritoInterface, cantidad: number }>();

    seleccion.forEach(p => {
      if (resumenMap.has(p.id_platillo)) {
        resumenMap.get(p.id_platillo)!.cantidad += 1;
      } else {
        resumenMap.set(p.id_platillo, { platillo: p, cantidad: 1 });
      }
    });

    this.resumenSeleccion = Array.from(resumenMap.values());

    // 🔹 Calcular total
    this.total = this.resumenSeleccion.reduce(
      (acc, item) => acc + item.platillo.precio_unitario * item.cantidad,
      0
    );

    console.log("Total:", this.total);
  }

  // 🔹 Enviar carrito temporal con todos los datos necesarios
  encargarPedido() {
    if (this.productosSeleccionados.length === 0) {
      console.warn('No hay productos seleccionados');
      return;
    }

    // 🔹 Crear lista_producto según el formato esperado
    const lista_producto = this.resumenSeleccion.map(item => ({
      nombre: item.platillo.Nombre_platillo, // asegúrate que tu modelo CarritoInterface tenga esta propiedad
      cant: item.cantidad
    }));

    const data = {
      idscarrito: this.idscarrito,
      precio: this.total,
      lista_producto
    };

    console.log(data);

    this.carritoService.agregar_temporal(data).subscribe({
      next: (res) => {
        console.log('Carrito temporal guardado:', res);
        this.router.navigate(['/direccion-pago']);
      },
      error: (err) => {
        console.error('Error al guardar el carrito temporal:', err);
      }
    });
  }
}
