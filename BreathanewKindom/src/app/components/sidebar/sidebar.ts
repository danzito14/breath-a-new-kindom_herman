import { Component, Input, OnInit, NgZone, ChangeDetectorRef } from '@angular/core';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Categoria, CategoriasService } from '../../services/categorias/categorias-service';
import { MaxAndMinPrice, maxandmin } from '../../services/home/max-and-min-price';
import { FormsModule } from '@angular/forms';
import { debounceTime, Subject } from 'rxjs';


@Component({
  selector: 'app-sidebar',
  imports: [CommonModule, FormsModule],
  standalone: true,
  templateUrl: './sidebar.html',
  styleUrls: ['./sidebar.css'],
  animations: [
    trigger('slideInOut', [
      state('hidden', style({
        transform: 'translateX(100%)',
        opacity: 0
      })),
      state('visible', style({
        transform: 'translateX(0)',
        opacity: 1
      })),
      transition('hidden => visible', [
        animate('350ms ease-out')
      ]),
      transition('visible => hidden', [
        animate('350ms ease-in')
      ])
    ])
  ]
})
export class Sidebar implements OnInit {
  @Input() isVisible = false;

  categoria: Categoria[] = [];
  prices: maxandmin = { min_price: 0, max_price: 0 };

  // valores actuales del rango de precio
  precioMin: number = 0;
  precioMax: number = 0;

  private precioSubject = new Subject<number>();

  //varaible para actualizar el input range en tiempo real
  rangoActual: number = this.precioMax / 2;
  constructor(
    private categoriaservice: CategoriasService,
    private cd: ChangeDetectorRef,
    private zone: NgZone,
    private maxandmin: MaxAndMinPrice,
    private router: Router
  ) {
    this.precioSubject.pipe(debounceTime(1000)).subscribe(valor => this.filtrarPorPrecio(this.prices.min_price, valor))
  }

  ngOnInit(): void {
    // cargar categorías
    this.categoriaservice.get_all_categorias().subscribe({
      next: (data) => {
        this.zone.run(() => {
          this.categoria = data;
          this.cd.detectChanges();
        });
      },
      error: (err) => console.log("Error al llamar al servidor", err)
    });

    // obtener precios máximo y mínimo
    this.maxandmin.get_min_and_max_price().subscribe({
      next: (dataprice) => {
        this.zone.run(() => {
          this.prices = dataprice;
          this.precioMin = dataprice.min_price;
          this.precioMax = dataprice.max_price;
          this.cd.detectChanges();
        });
      },
      error: (err) => console.log("Error al llamar al servicio", err)
    });
  }

  // 🔍 Buscar texto libre
  buscarTexto(texto: string) {
    const filtro = { texto };
    this.router.navigate(['/result'], { queryParams: { search: texto } });
    console.log(filtro)
  }

  // 🏷️ Filtrar por categoría
  filtrarCategoria(categoria: number, descripcion_cat: string) {
    this.router.navigate(["/result"], { queryParams: { categoria: categoria, descripcion_cat: descripcion_cat } });
    console.log(descripcion_cat);
  }
  onSliderChange(valor: number) {
    this.rangoActual = valor;
    this.precioSubject.next(valor); // manda el valor al "debounce"
  }

  filtrarPorPrecio(min: number, max: number) {
    console.log('Llamada al backend con rango:', min, max);

    this.router.navigate(["/result"], { queryParams: { minprice: min, maxprice: max } });
  }

  buscar_filtro(filtro: string) {
    console.log("filtro aca usado", filtro)
    this.router.navigate(["/result"], { queryParams: { filtro_especial: filtro } });
  }
}
