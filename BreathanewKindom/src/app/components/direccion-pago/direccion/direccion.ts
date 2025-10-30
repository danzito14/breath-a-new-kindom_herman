import { Component } from '@angular/core';
import { CarritoService, DireccionInterface } from '../../../services/carrito/carrito';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { SoloNumerosDirective } from "../../../directives/register/solo-numeros-code";

@Component({
  selector: 'app-direccion',
  imports: [CommonModule, ReactiveFormsModule, SoloNumerosDirective],
  templateUrl: './direccion.html',
  styleUrl: './direccion.css'
})
export class Direccion {
  form!: FormGroup;
  colonias: string[] = [];

  constructor(private carritoService: CarritoService, private fb: FormBuilder) { }

  ngOnInit() {
    this.form = this.fb.group({
      alias: ['', Validators.required],
      Calle: ['', Validators.required],
      No_ext: ['', Validators.required],
      No_int: [''],                 // opcional
      CP: ['', Validators.required],
      Colonia: ['', Validators.required],
      Municipio: ['', Validators.required],
      Estado: ['', Validators.required],
      Ciudad: [''],                 // opcional
      instrucciones_add: ['']         // opcional
    });
  }

  obtener_direccion(CP: string) {
    this.carritoService.buscarPorCP(CP).subscribe({
      next: (res: any[]) => {
        if (res && res.length > 0) {
          this.colonias = res.map(r => r.Colonia);
          const info = res[0];
          this.form.patchValue({
            Municipio: info.Municipio,
            Estado: info.Estado,
            Ciudad: info.Ciudad
          });
        } else {
          this.colonias = [];
        }
      },
      error: (err) => console.error('Error al buscar CP:', err)
    });
  }

  guardar_direccion() {
    if (this.form.invalid) {
      console.warn('Faltan campos obligatorios');
      this.form.markAllAsTouched();
      return;
    }

    this.carritoService.agregar_direccion(this.form.value).subscribe({
      next: (res) => console.log('Dirección guardada:', res),
      error: (err) => console.error('Error al guardar dirección:', err)
    });
  }

  regresar() {
    window.history.back();
  }

}
