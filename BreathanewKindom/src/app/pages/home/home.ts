import { Component } from '@angular/core';
import { TarjetaProduct } from "../../components/tarjeta-product/tarjeta-product";
import { TarjetaOferta } from "../../components/tarjeta-oferta/tarjeta-oferta";

@Component({
  selector: 'app-home',
  imports: [TarjetaProduct, TarjetaOferta],
  templateUrl: './home.html',
  styleUrl: './home.css'
})
export class Home {

}
