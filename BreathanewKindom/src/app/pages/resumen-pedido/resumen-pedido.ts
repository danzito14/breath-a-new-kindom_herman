import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, NgZone, OnInit } from '@angular/core';
import { TarjetaCarrito } from '../../components/tarjeta-carrito/tarjeta-carrito';
import { CarritoService, TemporalInterface } from '../../services/carrito/carrito';
import { Router } from 'express';

@Component({
  selector: 'app-resumen-pedido',
  imports: [CommonModule, TarjetaCarrito],
  templateUrl: './resumen-pedido.html',
  styleUrl: './resumen-pedido.css'
})
export class ResumenPedido implements OnInit {
  resumen: TemporalInterface[] = [];
  idscarrito: any[] = [];
  ticket: any[] = [];

  constructor(private carritoService: CarritoService,
    private router: Router,
    private zone: NgZone,
    private cd: ChangeDetectorRef
  ) { }

  ngOnInit() {
    // this.obtener_resumen();
  }

  regresar() {
    window.history.back();
  }

  // obtener_resumen() {
  //   this.carritoService.get_resumen_pedido().subscribe(res => {
  //     this.zone.run(() => {
  //       console.log(res);
  //       this.resumen = res
  //       this.cd.detectChanges
  //     });
  //   });
  // }

}
