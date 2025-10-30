import {
  Directive, HostListener, Renderer2, forwardRef
} from '@angular/core';
import {
  NG_VALIDATORS, Validator, AbstractControl, ValidationErrors
} from '@angular/forms';


@Directive({
  selector: '[appMesFecha]',
  providers: [
    {
      provide: NG_VALIDATORS,
      useExisting: forwardRef(() => MesFecha),
      multi: true
    }
  ]

})
export class MesFecha {
  constructor(private renderer: Renderer2) { }

  validate(control: AbstractControl): ValidationErrors | null {
    const value = control.value?.trim();
    const regex = /^(0[1-9]|1[0-2])\/\d{2}$/;
    if (!regex.test(value)) {
      return { mesAnioInvalido: true };
    }

    const [mesStr, anioStr] = value.split('/');
    const mes = parseInt(mesStr, 10);
    const anio = parseInt(anioStr, 10);

    const ahora = new Date();
    const mesActual = ahora.getMonth() + 1; // 0-indexed
    const anioActual = ahora.getFullYear() % 100; // Últimos dos dígitos

    const fechaIngresada = anio * 100 + mes;
    const fechaActual = anioActual * 100 + mesActual;

    if (fechaIngresada < fechaActual) {
      return { fechaAnterior: true };
    }

    return null;
  }

  @HostListener('input', ['$event'])
  onInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    let raw = input.value.replace(/\D/g, '').slice(0, 4);

    if (raw.length >= 3) {
      raw = raw.slice(0, 2) + '/' + raw.slice(2);
    }

    input.value = raw;

    const isValid = this.validate({ value: raw } as AbstractControl) === null;
    const color = isValid ? '#D0AF43' : '#773832';
    this.renderer.setStyle(input, 'border-bottom', `2px solid ${color}`);
  }


}
