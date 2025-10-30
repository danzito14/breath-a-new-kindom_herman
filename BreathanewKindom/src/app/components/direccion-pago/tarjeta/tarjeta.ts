import { Component } from '@angular/core';
import { MesFecha } from "../../../directives/tarjeta/mes-fecha";
import { TarjetaNumeros } from '../../../directives/tarjeta/tarjeta-numeros';
import { TarjetaCvv } from "../../../directives/tarjeta/tarjeta-cvv";
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from "@angular/forms";
import { CarritoService, TarjetaInterface } from '../../../services/carrito/carrito';

@Component({
  selector: 'app-tarjeta',
  imports: [MesFecha, TarjetaNumeros, TarjetaCvv, CommonModule,
    FormsModule, ReactiveFormsModule],
  templateUrl: './tarjeta.html',
  styleUrl: './tarjeta.css'
})
export class Tarjeta {
  form!: FormGroup;

  constructor(private carritoService: CarritoService, private fb: FormBuilder) { }


  ngOnInit() {
    this.form = this.fb.group({
      titular: ['', Validators.required],
      fecha: ['', Validators.required],
      cvv: ['', Validators.required],
      numero_tarjeta: ['', Validators.required],
    });
  }

  guardar_tarjeta() {
    if (this.form.invalid) {
      console.warn('Faltan campos obligatorios');
      this.form.markAllAsTouched();
      return;
    }

    const tarjetaCompleta = this.form.get('numero_tarjeta')?.value || '';
    const ultimos4 = tarjetaCompleta.slice(-4);
    const titular = this.form.get('titular')?.value || '';
    const fecha_exp = this.form.get('fecha')?.value || '';

    const nueva_tarjeta: TarjetaInterface = {
      titular: titular,
      num_tarjeta: ultimos4,
      fecha_exp: fecha_exp
    }

    this.carritoService.agregar_tarjeta(nueva_tarjeta).subscribe({
      next: (res) => console.log('Tarjeta guardada:', res),
      error: (err) => console.error('Error al guardar la tarjeta:', err)
    });
  }

  regresar() {
    window.history.back();
  }


}
