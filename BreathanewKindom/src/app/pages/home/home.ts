import { ChangeDetectionStrategy, ChangeDetectorRef, Component, NgZone, OnInit } from '@angular/core';
import { TarjetaProduct } from "../../components/tarjeta-product/tarjeta-product";
import { TarjetaOferta } from "../../components/tarjeta-oferta/tarjeta-oferta";
import { ProductosService, Producto, CombosInterface } from '../../services/home/productosService';
import { TarjetaCombos } from '../../components/tarjeta-combos/tarjeta-combos';

@Component({
  selector: 'app-home',
  imports: [TarjetaProduct, TarjetaOferta, TarjetaCombos],
  templateUrl: './home.html',
  styleUrls: ['./home.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class Home implements OnInit {

  productos: Producto[] = [];
  combos: CombosInterface[] = [];

  constructor(private productosService: ProductosService,
    private cd: ChangeDetectorRef,
    private zone: NgZone
  ) { }

  ngOnInit(): void {
    this.cargarProductos();
    this.cargarCombos();
  }

  cargarProductos() {
    this.productosService.get_all_Productos().subscribe({
      next: (data) => {
        this.zone.run(() => {
          this.productos = data;
          this.cd.markForCheck();
        });
      },
      error: (err) => console.error('Error cargando productos:', err)
    });
  }

  cargarCombos() {
    this.productosService.get_all_combos().subscribe({
      next: (data) => {
        // Ejecutar dentro de NgZone pero sin forzar detección manual
        this.zone.run(() => {
          this.combos = data;
          // Marca para verificación en el siguiente ciclo
          this.cd.markForCheck();
        });
      },
      error: (err) => console.error(err)
    });
  }

}
