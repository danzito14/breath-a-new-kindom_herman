import { Component } from '@angular/core';
import { OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { OfertasService, Oferta_home } from '../../services/home/ofertas-service';

@Component({
  selector: 'app-tarjeta-oferta',
  imports: [CommonModule],
  templateUrl: './tarjeta-oferta.html',
  styleUrl: './tarjeta-oferta.css'
})
export class TarjetaOferta implements OnInit {
  ofertaproductos: Oferta_home[] = []

  constructor(private ofertasservice: OfertasService) { }

  ngOnInit(): void {
    this.ofertasservice.get_all_product_for_home().subscribe({
      next: (data) => this.ofertaproductos = data,
      error: (err) => console.error('Error al llamar al servicio de Ofertas Home')
    })
  }
}
