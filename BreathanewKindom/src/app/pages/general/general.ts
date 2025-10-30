import { ChangeDetectorRef, Component, NgZone, OnInit } from '@angular/core';
import { PersonalizarPlatillo } from "../../components/personalizar-platillo/personalizar-platillo";
import { ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';
import { idsCombo, ProductosService } from '../../services/home/productosService';
import { Tarjeta } from "../../components/direccion-pago/tarjeta/tarjeta";
import { Direccion } from "../../components/direccion-pago/direccion/direccion";

@Component({
  selector: 'app-general',
  imports: [PersonalizarPlatillo, CommonModule, Tarjeta, Direccion],
  templateUrl: './general.html',
  styleUrl: './general.css'
})
export class General implements OnInit {
  idsPlatillos: any[] | null = null;
  id_productoocombo: string = "";
  accion: string = "";
  tipo: string = "";
  destino: string = "";
  carrito: boolean = false;
  agregar: string = "";

  //guardar los resultados de la busqueda
  resultado_busqueda: any[] | null = null;

  constructor(private route: ActivatedRoute,
    private cd: ChangeDetectorRef,
    private zone: NgZone,
    private productosService: ProductosService
  ) { }

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      // const rawIds = params['idplatillos'] || '';
      // this.idsPlatillos = rawIds ? rawIds.split(',') : null;  // convierte a array
      this.id_productoocombo = params['id_producto'] || '';
      this.accion = params['accion'] || '';
      this.tipo = params['tipo'] || '';
      this.destino = params['destino'] || '';
      this.agregar = params['agregar'] || '';

      this.filtrar_resultados();
    });
  }


  filtrar_resultados() {
    switch (this.accion) {
      case 'personalizar_plato':
        this.carrito = this.destino === 'carrito' ? true : false;
        if (this.tipo === 'combo') {
          this.productosService.get_ids_combo(this.id_productoocombo)
            .subscribe({
              next: (ids: idsCombo[]) => {
                this.idsPlatillos = ids.map(i => i.id_platillo);
                this.cd.detectChanges(); // fuerza a Angular a detectar cambios
                console.log(this.idsPlatillos);
              },
              error: (err) => console.error(err)
            });

        } else if (this.tipo === 'plato') {
          this.idsPlatillos = [this.id_productoocombo]; // array con un solo elemento
        }
        console.log(this.idsPlatillos);
        console.log(this.id_productoocombo);
        break;

      default:
        break;
    }
  }
}
