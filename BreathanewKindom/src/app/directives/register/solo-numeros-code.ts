import { Directive, ElementRef, Renderer2, HostListener } from '@angular/core';

@Directive({
  selector: '[soloNumeros]',
  standalone: true
})
export class SoloNumerosDirective {
  constructor(private el: ElementRef, private renderer: Renderer2) { }

  @HostListener('input', ['$event'])
  onInput(event: Event): void {
    const input = this.el.nativeElement;

    // Eliminar letras y limitar a 6 caracteres
    const valor = input.value.replace(/[^0-9]/g, '').slice(0, 5);
    input.value = valor;

    // Cambiar borde según longitud
    if (valor.length === 5) {
      this.renderer.setStyle(input, 'border-bottom', '2px solid #D0AF43');
    } else {
      this.renderer.setStyle(input, 'border-bottom', '2px solid #773832');
    }
  }
}