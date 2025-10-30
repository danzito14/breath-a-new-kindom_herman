import { ChangeDetectorRef, Component, Input, NgZone, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Filtros } from '../../services/filtrado/filtros';
import { TarjetaProduct } from '../../components/tarjeta-product/tarjeta-product';
import { CommonModule } from '@angular/common';
import { TarjetaOferta } from '../../components/tarjeta-oferta/tarjeta-oferta';
import { TarjetaCombos } from '../../components/tarjeta-combos/tarjeta-combos';
import { FavoritosService } from '../../services/home/favoritos-service';

@Component({
  selector: 'app-result',
  templateUrl: './result.html',
  styleUrls: ['./result.css'],
  imports: [TarjetaProduct, TarjetaOferta, CommonModule, TarjetaCombos]
})
export class Result implements OnInit {
  titulo: string = "Sin resultados";
  search: string | null = null;
  categoria: number | null = null;
  descripcion_cat: string | null = null;
  minprice: number | null = null;
  maxprice: number | null = null;
  filtro_especial: string = "normal";


  //para guardar los productos de la busqueda
  resultadoProducto: any[] | null = null;
  resultadoProductoCombo: any[] | null = null;


  constructor(private route: ActivatedRoute,
    private filtroproductoService: Filtros,
    private favoritosservice: FavoritosService,
    private cd: ChangeDetectorRef,
    private zone: NgZone
  ) { }

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      this.search = params['search'] || null;
      this.categoria = params['categoria'] || null;
      this.descripcion_cat = params['descripcion_cat'] || null;
      this.minprice = params['minprice'] ? +params['minprice'] : null;
      this.maxprice = params['maxprice'] ? +params['maxprice'] : null;
      this.filtro_especial = params['filtro_especial'] || 'normal';

      this.filtrar_resultados();
    });
  }

  filtrar_resultados() {
    if (this.search) {
      this.titulo = `Resultado de ${this.search}`;
      this.busqueda_por_texto(this.search);
    }
    else if (this.categoria) {
      this.titulo = `Categoría: ${this.descripcion_cat}`;
      this.buscar_por_categoria(this.categoria);
    }
    else if (this.minprice !== null && this.maxprice !== null) {
      this.filtro_especial = 'precio';
      this.buscar_por_precio(this.minprice, this.maxprice);
      this.buscar_por_precio_combo(this.minprice, this.maxprice);
    }
    else if (this.filtro_especial === 'oferta') {
      this.filtro_especial = 'oferta';
      this.titulo = 'Platillos en oferta';
    }
    else if (this.filtro_especial === 'combo') {
      this.filtro_especial = 'combo';
      this.titulo = 'Nuestros Combos';
    }
    else if (this.filtro_especial === 'favoritos') {
      this.cargarFavoritos();
    }
    else {
      this.titulo = 'Sin resultados';
      this.resultadoProducto = [];
    }

    console.log(this.titulo);
  }


  busqueda_por_texto(search: string) {
    this.filtroproductoService.get_productos_by_name(search).subscribe({
      next: (productos) => {
        setTimeout(() => {

          this.zone.run(() => {
            this.resultadoProducto = productos;
          })
          this.cd.detectChanges();
        });
      },
      error: (err) => console.error("Error al obenter los productos", err)
    })
  }

  buscar_por_categoria(cat: number) {
    this.filtroproductoService.get_productos_by_categoria(cat).subscribe({
      next: (productos) => {
        setTimeout(() => {

          this.zone.run(() => {
            this.resultadoProducto = productos;
          })
          this.cd.detectChanges();
        });
      },
      error: (err) => console.error("Error al obenter los productos", err)
    })
  }



  buscar_por_precio(min_price: number, max_price: number) {
    this.filtroproductoService.get_productos_by_price(min_price, max_price).subscribe({
      next: (productos) => {
        setTimeout(() => {

          this.zone.run(() => {
            this.resultadoProducto = productos;
          })
          this.cd.detectChanges();
        });
      },
      error: (err) => console.error("Error al obenter los productos", err)
    })
  }

  buscar_por_precio_combo(min_price: number, max_price: number) {
    this.filtroproductoService.get_combos_by_price(min_price, max_price).subscribe({
      next: (productos) => {
        setTimeout(() => {

          this.zone.run(() => {
            this.resultadoProductoCombo = productos;
          })
          this.cd.detectChanges();
        });
      },
      error: (err) => console.error("Error al obenter los productos", err)
    })
  }


  cargarFavoritos() {
    this.filtro_especial = 'favoritos';
    this.titulo = 'Favoritos';
    this.favoritosservice.get_favoritos_user().subscribe({
      next: (data) => {
        this.zone.run(() => {
          this.resultadoProducto = data;
          this.cd.markForCheck();
        });
      },
      error: (err) => console.error('Error cargando productos:', err)
    });
  }

}
