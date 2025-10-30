import { Component, OnInit, NgZone, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FavoritosService, FavoritoInterface } from '../../services/home/favoritos-service';
import { OfertasService, Oferta_home, ProductoConFavorito } from '../../services/home/ofertas-service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-tarjeta-oferta',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tarjeta-oferta.html',
  styleUrls: ['./tarjeta-oferta.css'] // CORRECCIÓN
})

export class TarjetaOferta implements OnInit {

  productos: ProductoConFavorito[] = [];
  favoritos: FavoritoInterface[] = [];

  constructor(
    private ofertasservice: OfertasService,
    private favoritosService: FavoritosService,
    private cd: ChangeDetectorRef,
    private zone: NgZone,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.ofertasservice.get_all_product_for_home().subscribe({
      next: (productosData) => {
        this.favoritosService.get_favoritos_user().subscribe({
          next: (favoritosData) => {
            this.zone.run(() => {
              this.favoritos = favoritosData;

              this.productos = productosData.map(prod => {
                const fav = this.favoritos.find(f => f.id_platillo === prod.id_platillo);
                return {
                  ...prod,
                  isFavorite: !!fav,
                  id_favorito: fav ? fav.id_favorito : null
                } as ProductoConFavorito;
              });
            });
            this.cd.detectChanges();
          },
          error: (err) => console.error('Error al cargar favoritos', err)
        });
      },
      error: (err) => console.error('Error al cargar productos', err)
    });
  }
  // 🔹 Cambiar estado de favorito
  toggleFavorito(prod: ProductoConFavorito) {
    if (prod.isFavorite) {
      // Eliminar favorito
      this.favoritosService.eliminarFavorito(prod.id_favorito!).subscribe({
        next: () => {
          prod.isFavorite = false;
          prod.id_favorito = null;
          this.favoritos = this.favoritos.filter(f => f.id_favorito !== prod.id_favorito);
          this.cd.detectChanges();
        },
        error: (err) => console.error('Error al eliminar favorito', err)
      });
    } else {
      // Agregar favorito
      this.favoritosService.agregarFavorito(prod.id_platillo).subscribe({
        next: (res) => {
          prod.isFavorite = true;
          prod.id_favorito = res.id_favorito;
          this.favoritos.push(res);
          this.cd.detectChanges();
        },
        error: (err) => console.error('Error al agregar favorito', err)
      });
    }
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
