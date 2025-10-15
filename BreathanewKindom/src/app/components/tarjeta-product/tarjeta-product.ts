import { Component } from '@angular/core';
import { OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProductosService, Producto } from '../../services/home/productosService';

@Component({
  selector: 'app-tarjeta-product',
  imports: [CommonModule],
  templateUrl: './tarjeta-product.html',
  styleUrl: './tarjeta-product.css'
})
export class TarjetaProduct implements OnInit {
  productos: Producto[] = []

  constructor(private productosservice: ProductosService) { }

  ngOnInit(): void {
    this.productosservice.get_all_Productos().subscribe({
      next: (data) => this.productos = data,
      error: (err) => console.error('Error al llamar al servidor', err)
    })
  }
}
