import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { TarjetaCarrito } from '../../components/tarjeta-carrito/tarjeta-carrito';

@Component({
  selector: 'app-temporal',
  imports: [CommonModule, TarjetaCarrito],
  templateUrl: './temporal.html',
  styleUrls: ['./temporal.css', '../../app.css']
})
export class Temporal {

}
