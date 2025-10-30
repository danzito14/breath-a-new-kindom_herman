import {
  Directive, HostListener, Renderer2, forwardRef
} from '@angular/core';
import {
  NG_VALIDATORS, Validator, AbstractControl, ValidationErrors
} from '@angular/forms';

@Directive({
  selector: '[appTarjetaNumeros]',
  providers: [
    {
      provide: NG_VALIDATORS,
      useExisting: forwardRef(() => TarjetaNumeros),
      multi: true
    }
  ]
})
export class TarjetaNumeros {

  constructor(private renderer: Renderer2) { }

  validate(control: AbstractControl): ValidationErrors | null {
    const rawValue = control.value?.replace(/\s+/g, '');
    const isValid = /^\d{13,19}$/.test(rawValue);
    return isValid ? null : { numeroTarjetaInvalido: true };
  }

  @HostListener('input', ['$event'])
  onInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const raw = input.value.replace(/\D/g, '').slice(0, 19);
    const formatted = raw.replace(/(.{4})/g, '$1 ').trim();
    input.value = formatted;

    const borderColor = formatted.replace(/\s/g, '').length >= 13
      ? '#D0AF43'
      : '#773832';

    this.renderer.setStyle(input, 'border-bottom', `2px solid ${borderColor}`);
  }

}
