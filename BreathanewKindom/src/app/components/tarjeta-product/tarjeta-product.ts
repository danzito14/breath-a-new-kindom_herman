import { Component, OnInit, Input, OnChanges, SimpleChanges, ChangeDetectionStrategy, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BehaviorSubject, Observable, combineLatest, Subject } from 'rxjs';
import { map, switchMap, takeUntil, take } from 'rxjs/operators';
import { ProductosService, ProductoConFavorito, Producto } from '../../services/home/productosService';
import { FavoritosService } from '../../services/home/favoritos-service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-tarjeta-product',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tarjeta-product.html',
  styleUrls: ['./tarjeta-product.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TarjetaProduct implements OnInit, OnChanges, OnDestroy {
  @Input() productosExternos: ProductoConFavorito[] | Producto[] = [];
  @Input() mostrarFavorito: boolean = true;
  @Input() autoCargar: boolean = true;
  @Input() favoritospage: boolean = false;

  productos$: Observable<ProductoConFavorito[]>;
  private productosSubject = new BehaviorSubject<ProductoConFavorito[]>([]);
  private destroy$ = new Subject<void>();

  tiposPlatillo: any[] = [];

  constructor(
    private productosService: ProductosService,
    private favoritosService: FavoritosService,
    private router: Router
  ) {
    this.productos$ = this.productosSubject.asObservable();
  }

  ngOnInit(): void {
    /*if (this.autoCargar && (!this.productosExternos || this.productosExternos.length === 0)) {
      this.cargarProductos();
    }*/
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['productosExternos'] && changes['productosExternos'].currentValue) {
      const productos = Array.isArray(changes['productosExternos'].currentValue)
        ? changes['productosExternos'].currentValue
        : [];

      combineLatest([
        this.favoritosService.get_favoritos_user().pipe(take(1)),
        this.productosService.get_tipo_paltillo().pipe(take(1))
      ])
        .pipe(takeUntil(this.destroy$))
        .subscribe(([favoritos, tipos]) => {
          this.tiposPlatillo = tipos;

          const productosConFavorito = productos.map(prod => {
            const fav = favoritos.find(f => f.id_platillo === (prod as any).id_platillo);
            return {
              ...prod,
              isFavorite: !!fav,
              id_favorito: fav?.id_favorito ?? null
            } as ProductoConFavorito;
          });

          this.productosSubject.next(productosConFavorito);
        });
    }
  }
  toggleFavorito(prod: ProductoConFavorito) {
    if (prod.isFavorite) {
      this.favoritosService.eliminarFavorito(prod.id_favorito!).pipe(take(1)).subscribe(() => {
        prod.isFavorite = false;
        prod.id_favorito = null;
        if (this.favoritospage) {
          // 👇 si estás en la página de favoritos, quita el producto de la lista
          const nuevaLista = this.productosSubject.value.filter(p => p.id_platillo !== prod.id_platillo);
          this.productosSubject.next([...nuevaLista]);
        } else {
          this.productosSubject.next([...this.productosSubject.value]);
        }
      });
    } else {
      this.favoritosService.agregarFavorito(prod.id_platillo).pipe(take(1)).subscribe(res => {
        prod.isFavorite = true;
        prod.id_favorito = res.id_favorito;
        this.productosSubject.next([...this.productosSubject.value]);
      });
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  get_color_tipo(prod: ProductoConFavorito): string {
    const tipo = this.tiposPlatillo.find(
      t => Number(t.id_tipo_platillo) === Number(prod.id_tipo_platillo)
    );
    return tipo?.color || '#d6b45a';
  }

  get_color_Categoria(prod: ProductoConFavorito): string {
    const tipo = this.tiposPlatillo.find(
      t => Number(t.id_tipo_platillo) === Number(prod.id_tipo_platillo)
    );
    return tipo?.descripcion || 'Platillo';
  }

  personalizar_plato(id_producto: string, tipo: string, destino: string) {
    this.router.navigate(["/general"], {
      queryParams: {
        id_producto: id_producto,  // lo convertimos en string "id1" que luego se convierte en array
        tipo: tipo,
        destino: destino,
        accion: "personalizar_plato"
      }
    });
  }

}
